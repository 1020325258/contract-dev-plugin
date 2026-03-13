# Spring AI Alibaba Agent Framework - 核心设计分析

## 1. Agent 类设计

### 1.1 Agent 基类

**文件路径**: `com.alibaba.cloud.ai.graph.agent.Agent`

**类职责**:
- 所有 Agent 的抽象基类
- 提供统一的执行接口（invoke、stream、schedule）
- 管理 StateGraph 和 CompiledGraph 的生命周期
- 处理消息输入转换

**核心属性**:
```java
protected String name;              // Agent 唯一标识
protected String description;       // Agent 能力描述
protected CompileConfig compileConfig;  // 编译配置
protected volatile CompiledGraph compiledGraph;  // 编译后的图
protected volatile StateGraph graph;  // 状态图
protected Executor executor;        // 执行器
```

**核心方法**:
```java
// 图初始化（子类实现）
protected abstract StateGraph initGraph() throws GraphStateException;

// 同步执行
public Optional<OverAllState> invoke(String message);
public Optional<OverAllState> invoke(UserMessage message);
public Optional<OverAllState> invoke(List<Message> messages);
public Optional<OverAllState> invoke(Map<String, Object> inputs);

// 流式执行
public Flux<NodeOutput> stream(String message);
public Flux<Message> streamMessages(String message);

// 调度执行
public ScheduledAgentTask schedule(Trigger trigger, Map<String, Object> input);
```

**设计模式**:
- **模板方法模式**: `initGraph()` 由子类实现具体图构建逻辑
- **延迟初始化**: `getGraph()` 和 `getAndCompileGraph()` 采用延迟加载

### 1.2 BaseAgent

**文件路径**: `com.alibaba.cloud.ai.graph.agent.BaseAgent`

**类职责**:
- 继承自 Agent
- 可转换为 Graph Node 的 Agent
- 支持输入输出 Schema 定义

**核心属性**:
```java
protected String inputSchema;       // 输入 Schema
protected Type inputType;           // 输入类型
protected String outputSchema;      // 输出 Schema
protected Class<?> outputType;      // 输出类型
protected String outputKey;         // 输出键
protected KeyStrategy outputKeyStrategy;  // 输出键策略
protected boolean includeContents;  // 是否包含上下文内容
protected boolean returnReasoningContents;  // 是否返回推理内容
```

**抽象方法**:
```java
public abstract Node asNode(boolean includeContents, boolean returnReasoningContents);
```

### 1.3 ReactAgent

**文件路径**: `com.alibaba.cloud.ai.graph.agent.ReactAgent`

**类职责**:
- 实现 ReAct (Reasoning and Acting) 模式
- 支持工具调用
- 支持结构化输出

**核心属性**:
```java
private ChatModel chatModel;        // 大模型
private String instruction;          // 系统指令
private List<ToolCallback> tools;    // 工具列表
private List<AgentHook> agentHooks;  // Agent Hooks
private List<ModelHook> modelHooks;  // Model Hooks
private List<Hook> hooks;            // 通用 Hooks
private List<Interceptor> interceptors;  // 拦截器
private CheckpointSaver saver;       // 状态持久化
```

**设计特点**:
- 内部构建包含 LLM Node 和 Tool Node 的 StateGraph
- 支持 Human-in-the-loop 中断
- 支持 Token 统计

---

## 2. FlowAgent 设计

### 2.1 FlowAgent 基类

**文件路径**: `com.alibaba.cloud.ai.graph.agent.flow.agent.FlowAgent`

**类职责**:
- 流程编排 Agent 的抽象基类
- 管理子 Agent 列表
- 委托图构建给具体策略

**核心属性**:
```java
protected List<Agent> subAgents;     // 子 Agent 列表
protected StateSerializer stateSerializer;  // 状态序列化器
protected List<Hook> hooks;          // Hooks
```

**核心方法**:
```java
// 子类实现具体图构建策略
protected abstract StateGraph buildSpecificGraph(FlowGraphBuilder.FlowGraphConfig config);
```

### 2.2 SequentialAgent

**文件路径**: `com.alibaba.cloud.ai.graph.agent.flow.agent.SequentialAgent`

**类职责**:
- 顺序执行多个子 Agent
- 前一个 Agent 的输出传递给下一个 Agent

**执行流程**:
```
START -> Agent1 -> Agent2 -> Agent3 -> END
```

**使用示例**:
```java
SequentialAgent blogAgent = SequentialAgent.builder()
    .name("blog_agent")
    .description("顺序执行写作和审核")
    .subAgents(List.of(writerAgent, reviewerAgent))
    .build();
```

### 2.3 ParallelAgent

**文件路径**: `com.alibaba.cloud.ai.graph.agent.flow.agent.ParallelAgent`

**类职责**:
- 并行执行多个子 Agent
- 合并各 Agent 的结果

**核心属性**:
```java
private final MergeStrategy mergeStrategy;  // 合并策略
private final Integer maxConcurrency;       // 最大并发数
```

**合并策略**:
```java
public interface MergeStrategy {
    Object merge(Map<String, Object> subAgentResults, OverAllState overallState);
}

// 内置策略:
// - DefaultMergeStrategy: 返回 Map
// - ListMergeStrategy: 返回 List
// - ConcatenationMergeStrategy: 字符串拼接
```

**执行流程**:
```
       ┌-> Agent1 ─┐
START ─┼-> Agent2 ─┼-> Merge -> END
       └-> Agent3 ─┘
```

**使用示例**:
```java
ParallelAgent parallelAgent = ParallelAgent.builder()
    .name("parallel_workflow")
    .description("并行执行多个创作任务")
    .subAgents(List.of(proseWriterAgent, poemWriterAgent, summaryAgent))
    .mergeStrategy(new ParallelAgent.ListMergeStrategy())
    .maxConcurrency(5)
    .build();
```

### 2.4 LoopAgent

**文件路径**: `com.alibaba.cloud.ai.graph.agent.flow.agent.LoopAgent`

**类职责**:
- 循环执行单个子 Agent
- 支持多种循环策略

**循环策略**:
```java
public interface LoopStrategy {
    boolean shouldContinue(OverAllState state);
}

// 内置策略:
// - CountLoopStrategy: 固定次数循环
// - ConditionLoopStrategy: 条件循环
// - ArrayLoopStrategy: 数组迭代
```

**执行流程**:
```
START -> [Condition Check] -> Agent -> [Condition Check] -> ... -> END
```

**使用示例**:
```java
LoopAgent loopAgent = LoopAgent.builder()
    .name("loop_agent")
    .description("循环执行直到满足条件")
    .loopStrategy(LoopMode.condition(messagePredicate))
    .subAgent(subAgent)
    .build();
```

### 2.5 SupervisorAgent

**文件路径**: `com.alibaba.cloud.ai.graph.agent.flow.agent.SupervisorAgent`

**类职责**:
- 监督者模式，由主 Agent 决定路由
- 支持动态选择子 Agent

**核心属性**:
```java
private final ChatModel chatModel;    // 大模型
private final ReactAgent mainAgent;   // 主决策 Agent
```

**执行流程**:
```
START -> MainAgent -> [Route Decision] -> SubAgent1 -> MainAgent -> ...
                                        -> SubAgent2 -> MainAgent -> ...
                                        -> FINISH -> END
```

**使用示例**:
```java
SupervisorAgent supervisorAgent = SupervisorAgent.builder()
    .name("supervisor")
    .description("监督者模式")
    .mainAgent(mainAgent)
    .subAgents(List.of(agent1, agent2, agent3))
    .build();
```

---

## 3. Hook 机制设计

### 3.1 Hook 接口层次

```
Hook (interface)
├── AgentHook - Agent 级别拦截
├── ModelHook - 模型调用拦截
└── ToolInjection - 工具注入
```

### 3.2 HookPosition

**文件路径**: `com.alibaba.cloud.ai.graph.agent.hook.HookPosition`

**拦截位置**:
- `PRE_MODEL`: 模型调用前
- `POST_MODEL`: 模型调用后
- `PRE_TOOL`: 工具调用前
- `POST_TOOL`: 工具调用后

### 3.3 内置 Hook 实现

| Hook 类 | 功能 |
|---------|------|
| `HumanInTheLoopHook` | 人机交互中断 |
| `SummarizationHook` | 消息摘要压缩 |
| `ModelCallLimitHook` | 模型调用次数限制 |
| `ToolCallLimitHook` | 工具调用次数限制 |
| `PIIDetectionHook` | 敏感信息检测 |
| `InterruptionHook` | 中断处理 |
| `MessagesModelHook` | 消息处理 |

---

## 4. Interceptor 机制设计

### 4.1 Interceptor 接口

**文件路径**: `com.alibaba.cloud.ai.graph.agent.interceptor.Interceptor`

**类型**:
- `MODEL`: 模型拦截器
- `TOOL`: 工具拦截器

### 4.2 内置 Interceptor

| Interceptor 类 | 功能 |
|----------------|------|
| `ModelFallbackInterceptor` | 模型降级 |
| `ModelRetryInterceptor` | 模型重试 |
| `ToolRetryInterceptor` | 工具重试 |
| `ToolSelectionInterceptor` | 工具选择 |
| `ToolEmulatorInterceptor` | 工具模拟 |
| `ToolErrorInterceptor` | 工具错误处理 |
| `ContextEditingInterceptor` | 上下文编辑 |
| `TodoListInterceptor` | 待办列表 |
| `SkillsInterceptor` | 技能管理 |

---

## 5. Builder 模式设计

### 5.1 泛型 Builder 继承

```java
// 基类 Builder
public abstract class FlowAgentBuilder<T extends FlowAgent, B extends FlowAgentBuilder<T, B>> {
    protected String name;
    protected String description;
    protected List<Agent> subAgents;
    // ...

    protected abstract B self();
    protected abstract void validate();
    public abstract T doBuild();

    public B name(String name) {
        this.name = name;
        return self();
    }

    public final T build() {
        validate();
        return doBuild();
    }
}

// 具体子类 Builder
public static class SequentialAgentBuilder
    extends FlowAgentBuilder<SequentialAgent, SequentialAgentBuilder> {

    @Override
    protected SequentialAgentBuilder self() {
        return this;
    }

    @Override
    public SequentialAgent doBuild() {
        return new SequentialAgent(this);
    }
}
```

### 5.2 Builder 优势
- 类型安全的链式调用
- 编译期检查
- 子类可扩展特定属性
