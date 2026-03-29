# 多 Agent 协作编排模式

## 概述

在 SAA Graph 应用中实现多 Agent 协作的标准模式：以 ChatClient 为 Agent 核心、NodeAction 为调用封装、StateGraph 为编排骨架。本文档描述 DeepResearch 项目的完整实现。

## 整体架构

```
Layer 1: Agent 定义层          → AgentsConfiguration.java (ChatClient Bean)
Layer 2: Agent 封装层         → NodeAction 实现（CoordinatorNode 等）
Layer 3: Agent 编排层         → DeepResearchConfiguration.java (StateGraph)
Layer 4: Agent 执行层         → GraphProcess / ChatController (SSE 输出)
```

## Agent 定义层：ChatClient Bean

所有 Agent 都是 `ChatClient` Bean，在 `AgentsConfiguration` 中定义：

```java
// 核心 Agent 定义示例
@Bean
public ChatClient coordinatorAgent(ChatClient.Builder builder, PlannerTool plannerTool) {
    return builder
        .defaultOptions(ToolCallingChatOptions.builder()
            .internalToolExecutionEnabled(false).build())
        .defaultTools(plannerTool)  // 绑定 Tool
        .build();
}

@Bean
public ChatClient researchAgent(ChatClient.Builder builder) {
    return builder
        .defaultSystem(ResourceUtil.loadResourceAsString(researcherPrompt))
        .defaultToolNames(JinaCrawlerConstants.TOOL_NAME)
        .build();
}

@Bean
public ChatClient coderAgent(ChatClient.Builder builder, PythonReplTool tool) {
    return builder
        .defaultSystem(ResourceUtil.loadResourceAsString(coderPrompt))
        .defaultTools(tool)  // PythonReplTool
        .defaultToolCallbacks(mcpCallbacks)  // MCP 工具
        .build();
}
```

**Agent 清单**：

| Agent | Prompt 模板 | 绑定的 Tool | 用途 |
|---|---|---|---|
| coordinatorAgent | coordinator.md | PlannerTool | 意图识别，触发深度研究 |
| plannerAgent | planner.md | 无 | 制定研究计划，输出 JSON Plan |
| researchAgent | researcher.md | JinaCrawler | 执行研究任务，搜索+爬取 |
| reporterAgent | reporter.md | 无 | 汇总生成最终报告 |
| coderAgent | coder.md | PythonReplTool + MCP | 执行数据处理任务 |
| backgroundAgent | background.md | 无 | 背景调查搜索 |
| reflectionAgent | reflection.md | 无 | 反思评估（判断结果质量） |

**Smart Agent（可选）**：
```yaml
spring.ai.alibaba.deepresearch.smart-agents.enabled: true
```
- academicResearchAgent、lifestyleTravelAgent、encyclopediaAgent、dataAnalysisAgent

## Agent 封装层：NodeAction 实现

每个 Node 是一个 `NodeAction` 实现，内部持有对应的 ChatClient：

```java
public class CoordinatorNode implements NodeAction {
    private final ChatClient coordinatorAgent;

    @Override
    public Map<String, Object> apply(OverAllState state) {
        // 1. 构建消息
        List<Message> messages = new ArrayList<>();
        TemplateUtil.addShortUserRoleMemory(messages, state);
        messages.add(TemplateUtil.getMessage("coordinator"));
        messages.add(new UserMessage(query));

        // 2. 调用 Agent
        ChatResponse response = coordinatorAgent.prompt()
            .messages(messages).call().chatResponse();

        // 3. 判断是否触发工具调用
        if (assistantMessage.getToolCalls() != null) {
            return Map.of(
                "coordinator_next_node", "rewrite_multi_query",
                "deep_research", true
            );
        }
        return Map.of("output", text);
    }
}
```

**Node 清单**：

| Node | 持有 Agent | 职责 |
|---|---|---|
| CoordinatorNode | coordinatorAgent | 意图识别 + 路由决策 |
| RewriteAndMultiQueryNode | rewriteAndMultiQueryAgent | 查询重写 + 多查询扩展 |
| BackgroundInvestigationNode | backgroundAgent | 并行多查询搜索 |
| PlannerNode | plannerAgent | 生成 Plan JSON |
| ResearcherNode | researchAgent + SmartAgent | 执行 RESEARCH 类型 step |
| CoderNode | coderAgent | 执行 PROCESSING 类型 step |
| ReporterNode | reporterAgent | 生成最终报告 |

## 核心 Agent 分工

### Coordinator：意图识别

```java
// coordinator.md 核心指令
- 处理直接闲聊（问候、简单对话）
- 拒绝不安全请求
- 其他问题 → 调用 PlannerTool 触发深度研究

// Node 判断逻辑
if (assistantMessage.getToolCalls() != null) {
    deepResearch = true;  // 触发工具调用 = 需要深度研究
}
```

### Planner：制定研究计划

```java
// planner.md 输出 JSON 格式 Plan
{
  "has_enough_context": false,
  "thought": "用户问题的理解",
  "title": "研究计划标题",
  "steps": [
    { "title": "步骤1", "description": "具体数据点", "need_web_search": true, "step_type": "research" },
    { "title": "步骤2", "description": "计算任务", "need_web_search": false, "step_type": "processing" }
  ]
}

// 使用 BeanOutputConverter 解析 JSON
BeanOutputConverter<Plan> converter = new BeanOutputConverter<>(new ParameterizedTypeReference<Plan>() {});
Flux<ChatResponse> stream = plannerAgent.prompt(converter.getFormat()).messages(messages).stream().chatResponse();
```

### Researcher：信息收集

```java
// 动态选择 SmartAgent
AgentSelectionResult result = smartAgentSelectionHelper.selectSmartAgent(questionContent, state, researchAgent);
ChatClient selectedAgent = result.isSmartAgent() ? result.getSelectedAgent() : researchAgent;

// 反射重试机制
if (reflectionProcessor != null) {
    ReflectionHandleResult handleResult = reflectionProcessor.handleReflection(step, nodeName, "researcher");
    if (!shouldContinueAfterReflection(handleResult)) return;
}
```

### Reporter：报告生成

```java
// 消息构建顺序
messages.add(背景调查结果);           // background_investigation_results
messages.add(Researcher 内容);       // researcher_content_N
messages.add(Coder 内容);            // coder_content_N
if (useProfessionalKb) messages.add(RAG 内容);  // rag_content
```

## 协作流程

```
START → short_user_role_memory → coordinator
                                    ↓ 触发工具调用
                            rewrite_multi_query → background_investigator
                                    ↓
                            planner → information
                                    ↓ auto_accepted_plan
                            research_team ←──┐
                                    ↓          │
                            parallel_executor ←┘ (循环)
                                    ↓
                researcher_0..N / coder_0..N (并行执行)
                                    ↓
                            professional_kb_decision
                                    ↓
                            reporter → END
```

## 关键代码模式

### 流式调用 + FluxConverter

```java
Flux<ChatResponse> streamResult = agent.prompt().messages(messages).stream().chatResponse();

Flux<GraphResponse<StreamingOutput>> generator = FluxConverter.builder()
    .startingNode(prefix)
    .startingState(state)
    .mapResult(response -> Map.of("result_key", value))
    .buildWithChatResponse(streamResult);

return Map.of("result_key", generator);  // 返回 Flux 触发流式推送
```

### Tool 动态绑定

```java
// MCP 工具动态绑定
AsyncMcpToolCallbackProvider mcpProvider = mcpFactory.createProvider(state, "researchAgent");
if (mcpProvider != null) {
    requestSpec = requestSpec.toolCallbacks(mcpProvider.getToolCallbacks());
}
```

### Smart Agent 动态选择

```java
AgentSelectionResult result = smartAgentSelectionHelper.selectSmartAgent(
    questionContent, state, defaultAgent);
ChatClient selectedAgent = result.isSmartAgent()
    ? result.getSelectedAgent()   // 专业领域 Agent
    : defaultAgent;              // 通用 Agent
```

## 相关链接

- [dispatcher-routing-pattern.md](./dispatcher-routing-pattern.md) - 节点路由设计
- [streaming-output-pattern.md](./streaming-output-pattern.md) - 流式输出集成
- [memory-architecture.md](./memory-architecture.md) - 记忆架构