# Spring AI Alibaba Agent Framework - 功能开发指南

## 1. 快速开始

### 1.1 环境准备

**Maven 依赖**:
```xml
<dependency>
    <groupId>com.alibaba.cloud.ai</groupId>
    <artifactId>spring-ai-alibaba-agent-framework</artifactId>
</dependency>
```

**基本配置**:
```java
// 创建 ChatModel
DashScopeApi dashScopeApi = DashScopeApi.builder()
    .apiKey(System.getenv("AI_DASHSCOPE_API_KEY"))
    .build();

ChatModel chatModel = DashScopeChatModel.builder()
    .dashScopeApi(dashScopeApi)
    .build();
```

### 1.2 创建第一个 Agent

```java
// 创建简单的 ReactAgent
ReactAgent agent = ReactAgent.builder()
    .name("my_agent")
    .model(chatModel)
    .instruction("你是一个有用的AI助手")
    .build();

// 同步执行
Optional<OverAllState> result = agent.invoke("你好，请介绍一下自己");

// 流式执行
agent.streamMessages("你好").doOnNext(msg -> {
    System.out.println(msg.getText());
}).blockLast();
```

---

## 2. ReactAgent 开发

### 2.1 基本配置

```java
ReactAgent agent = ReactAgent.builder()
    .name("writer_agent")
    .model(chatModel)
    .description("可以写文章的AI助手")       // Agent 描述
    .instruction("你是一个知名的作家...")    // 系统指令
    .outputKey("article")                  // 输出键
    .includeContents(true)                 // 包含上下文
    .enableLogging(true)                   // 启用日志
    .build();
```

### 2.2 添加工具

```java
// 定义工具
@Tool(description = "获取指定城市的天气信息")
public String getWeather(@ToolParam(description = "城市名称") String city) {
    return "晴天，25度";
}

// 创建 ToolCallback
ToolCallback weatherTool = ToolCallbacks.from(new WeatherService());

// 添加到 Agent
ReactAgent agent = ReactAgent.builder()
    .name("weather_agent")
    .model(chatModel)
    .tools(List.of(weatherTool))
    .build();
```

### 2.3 结构化输出

**使用 outputSchema**:
```java
String jsonSchema = """
    {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "object",
        "properties": {
            "title": { "type": "string" },
            "content": { "type": "string" }
        },
        "additionalProperties": false
    }
    """;

ReactAgent agent = ReactAgent.builder()
    .name("structured_agent")
    .model(chatModel)
    .outputSchema(jsonSchema)
    .build();
```

**使用 outputType**:
```java
public record PoemOutput(String title, String content, String style) {}

ReactAgent agent = ReactAgent.builder()
    .name("poem_agent")
    .model(chatModel)
    .outputType(PoemOutput.class)
    .build();
```

### 2.4 状态持久化

```java
// 使用内存存储
ReactAgent agent = ReactAgent.builder()
    .name("persistent_agent")
    .model(chatModel)
    .saver(new MemorySaver())
    .build();

// 多轮对话
agent.invoke("第一轮：你好");
agent.invoke("第二轮：请记住我刚才说了什么");
```

---

## 3. SequentialAgent 开发

### 3.1 基本用法

```java
// 定义子 Agent
ReactAgent writerAgent = ReactAgent.builder()
    .name("writer_agent")
    .model(chatModel)
    .instruction("你是一个作家，请根据用户要求写作")
    .outputKey("article")
    .build();

ReactAgent reviewerAgent = ReactAgent.builder()
    .name("reviewer_agent")
    .model(chatModel)
    .instruction("你是一个评论家，请审核并改进文章")
    .outputKey("reviewed_article")
    .build();

// 创建顺序 Agent
SequentialAgent blogAgent = SequentialAgent.builder()
    .name("blog_agent")
    .description("顺序执行写作和审核")
    .subAgents(List.of(writerAgent, reviewerAgent))
    .build();

// 执行
Optional<OverAllState> result = blogAgent.invoke("写一篇关于春天的散文");
String article = result.get().value("article").get().toString();
String reviewed = result.get().value("reviewed_article").get().toString();
```

### 3.2 嵌套顺序 Agent

```java
// 子流程
SequentialAgent childProcess = SequentialAgent.builder()
    .name("child_process")
    .subAgents(List.of(step1Agent, step2Agent))
    .build();

// 父流程
SequentialAgent mainProcess = SequentialAgent.builder()
    .name("main_process")
    .subAgents(List.of(childProcess, finalAgent))
    .build();
```

### 3.3 使用模板变量

```java
ReactAgent reviserAgent = ReactAgent.builder()
    .name("reviser_agent")
    .model(chatModel)
    .includeContents(false)  // 不包含完整上下文
    .instruction("""
        你是一个排版专家，请修改以下文章：

        文章内容：
        {reviewed_article}
        """)
    .outputKey("revised_article")
    .build();
```

---

## 4. ParallelAgent 开发

### 4.1 基本用法

```java
// 定义多个专业 Agent
ReactAgent proseAgent = ReactAgent.builder()
    .name("prose_agent")
    .model(chatModel)
    .instruction("写散文")
    .outputKey("prose_result")
    .build();

ReactAgent poemAgent = ReactAgent.builder()
    .name("poem_agent")
    .model(chatModel)
    .instruction("写诗歌")
    .outputKey("poem_result")
    .build();

// 创建并行 Agent
ParallelAgent parallelAgent = ParallelAgent.builder()
    .name("parallel_agent")
    .description("并行创作")
    .subAgents(List.of(proseAgent, poemAgent))
    .build();
```

### 4.2 自定义合并策略

```java
// 实现自定义合并策略
public class CustomMergeStrategy implements ParallelAgent.MergeStrategy {
    @Override
    public Object merge(Map<String, Object> subAgentResults, OverAllState overallState) {
        // 自定义合并逻辑
        Map<String, Object> merged = new HashMap<>();
        merged.put("all_results", subAgentResults);
        return merged;
    }
}

// 使用自定义策略
ParallelAgent agent = ParallelAgent.builder()
    .name("custom_merge_agent")
    .subAgents(List.of(agent1, agent2))
    .mergeStrategy(new CustomMergeStrategy())
    .build();
```

### 4.3 并发控制

```java
ParallelAgent agent = ParallelAgent.builder()
    .name("limited_parallel_agent")
    .subAgents(List.of(agent1, agent2, agent3, agent4, agent5))
    .maxConcurrency(3)  // 最多同时执行3个
    .build();
```

---

## 5. LoopAgent 开发

### 5.1 固定次数循环

```java
LoopAgent loopAgent = LoopAgent.builder()
    .name("count_loop_agent")
    .description("循环执行3次")
    .loopStrategy(LoopMode.count(3))
    .subAgent(workerAgent)
    .build();
```

### 5.2 条件循环

```java
// 定义终止条件
Predicate<OverAllState> condition = state -> {
    Optional<Object> result = state.value("result");
    return result.isPresent() && result.get().toString().contains("完成");
};

LoopAgent loopAgent = LoopAgent.builder()
    .name("condition_loop_agent")
    .description("执行直到满足条件")
    .loopStrategy(LoopMode.condition(condition))
    .subAgent(workerAgent)
    .build();
```

### 5.3 数组迭代循环

```java
LoopAgent loopAgent = LoopAgent.builder()
    .name("array_loop_agent")
    .description("遍历数组处理")
    .loopStrategy(LoopMode.array("items", "current_item"))
    .subAgent(processorAgent)
    .build();
```

---

## 6. SupervisorAgent 开发

### 6.1 基本用法

```java
// 定义主决策 Agent
ReactAgent mainAgent = ReactAgent.builder()
    .name("supervisor_main")
    .model(chatModel)
    .instruction("""
        你是一个调度员，根据用户需求选择合适的处理者。
        可用的处理者：
        - writer: 负责写作
        - reviewer: 负责审核
        - FINISH: 任务完成

        请在回复中明确指定下一个处理者。
        """)
    .outputKey("supervisor_next")
    .build();

// 创建 SupervisorAgent
SupervisorAgent supervisorAgent = SupervisorAgent.builder()
    .name("supervisor")
    .description("监督者模式")
    .mainAgent(mainAgent)
    .subAgents(List.of(writerAgent, reviewerAgent))
    .build();
```

---

## 7. Hook 开发

### 7.1 创建自定义 Hook

```java
public class CustomModelHook implements ModelHook {

    @Override
    public HookPosition position() {
        return HookPosition.POST_MODEL;
    }

    @Override
    public int getPriority() {
        return 100;
    }

    @Override
    public Object apply(OverAllState state, AgentHook hook) {
        // 处理逻辑
        return null;
    }
}
```

### 7.2 添加 Hook 到 Agent

```java
ReactAgent agent = ReactAgent.builder()
    .name("hook_agent")
    .model(chatModel)
    .hooks(List.of(
        new CustomModelHook(),
        new HumanInTheLoopHook()
    ))
    .build();
```

### 7.3 Human-in-the-loop

```java
HumanInTheLoopHook hitlHook = HumanInTheLoopHook.builder()
    .interactionHandler(new ConsoleInteractionHandler())  // 控制台交互
    .build();

ReactAgent agent = ReactAgent.builder()
    .name("hitl_agent")
    .model(chatModel)
    .hooks(List.of(hitlHook))
    .build();
```

---

## 8. Interceptor 开发

### 8.1 创建自定义 Interceptor

```java
public class CustomToolInterceptor implements ToolInterceptor {

    @Override
    public InterceptorType type() {
        return InterceptorType.TOOL;
    }

    @Override
    public int getPriority() {
        return 50;
    }

    @Override
    public ToolCallResponse intercept(ToolCallExecutionContext context, ToolCallHandler next) {
        // 前置处理
        System.out.println("工具调用前: " + context.toolName());

        // 执行
        ToolCallResponse response = next.handle(context);

        // 后置处理
        System.out.println("工具调用结果: " + response.result());

        return response;
    }
}
```

### 8.2 添加 Interceptor 到 Agent

```java
ReactAgent agent = ReactAgent.builder()
    .name("interceptor_agent")
    .model(chatModel)
    .interceptors(List.of(
        new ToolRetryInterceptor(3),
        new CustomToolInterceptor()
    ))
    .build();
```

---

## 9. A2A 远程 Agent 开发

A2A (Agent-to-Agent) 允许 Agent 调用远程部署的其他 Agent，实现跨服务的 Agent 协作。

### 9.1 创建远程 Agent

```java
// 通过 AgentCard 创建远程 Agent
A2aRemoteAgent remoteAgent = A2aRemoteAgent.builder()
    .name("remote_weather_agent")
    .description("远程天气查询Agent")
    .agentCard(agentCard)  // AgentCard 包含远程 Agent 的信息
    .outputKey("weather_result")
    .build();

// 通过 AgentCardProvider 创建
A2aRemoteAgent remoteAgent = A2aRemoteAgent.builder()
    .name("remote_agent")
    .description("远程Agent")
    .agentCardProvider(agentCardProvider)  // 动态获取 AgentCard
    .build();
```

### 9.2 配置选项

```java
A2aRemoteAgent remoteAgent = A2aRemoteAgent.builder()
    .name("remote_agent")
    .description("远程Agent")
    .agentCard(agentCard)
    .instruction("额外的指令")      // 可选：添加额外指令
    .streaming(true)               // 启用流式输出
    .shareState(true)              // 共享状态
    .includeContents(true)         // 包含上下文
    .build();
```

### 9.3 在编排中使用

```java
// 将远程 Agent 作为子 Agent 使用
ReactAgent localAgent = ReactAgent.builder()
    .name("local_agent")
    .model(chatModel)
    .outputKey("local_result")
    .build();

SequentialAgent workflow = SequentialAgent.builder()
    .name("hybrid_workflow")
    .subAgents(List.of(localAgent, remoteAgent))  // 混合本地和远程 Agent
    .build();
```

### 9.4 注意事项

- `A2aRemoteAgent` 不支持 `schedule()` 方法
- 确保网络连接稳定
- AgentCard 信息应与远程 Agent 实际能力匹配
- 使用 Nacos 作为服务注册中心时，需要配置 `spring-ai-alibaba-starter-a2a-nacos`

---

## 10. 最佳实践

### 9.1 Agent 命名规范

- 使用有意义的名称，反映 Agent 的职责
- 名称在同一个图中必须唯一

### 9.2 输出键管理

- 每个子 Agent 应该有唯一的 `outputKey`
- 使用模板变量 `{outputKey}` 在后续 Agent 中引用

### 9.3 上下文控制

- 使用 `includeContents(false)` 控制上下文传递
- 使用 `returnReasoningContents(true)` 获取推理过程

### 9.4 错误处理

```java
try {
    Optional<OverAllState> result = agent.invoke("输入");
    if (result.isPresent()) {
        // 处理结果
    }
} catch (CompletionException e) {
    // 处理异常
    log.error("Agent 执行失败", e);
}
```

### 9.5 流式输出处理

```java
agent.streamMessages("输入")
    .doOnNext(msg -> System.out.print(msg.getText()))
    .doOnError(e -> log.error("流式输出错误", e))
    .doOnComplete(() -> System.out.println("\n完成"))
    .blockLast();
```
