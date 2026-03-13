# Spring AI Alibaba Agent Framework - 系统设计

## 1. 系统架构概览

```
┌─────────────────────────────────────────────────────────────────┐
│                      Agent Framework Layer                       │
├─────────────┬─────────────┬──────────────┬─────────────────────┤
│   Agent     │   FlowAgent  │   ReactAgent │      Tools          │
│   (Base)    │   (Orchestration)│(ReAct)    │                     │
├─────────────┴─────────────┴──────────────┴─────────────────────┤
│                     Hook & Interceptor Layer                     │
├───────────────────┬───────────────────┬─────────────────────────┤
│    Agent Hooks    │    Model Hooks    │    Tool Interceptors    │
├───────────────────┴───────────────────┴─────────────────────────┤
│                       Graph Core Layer                           │
├──────────────────────────────────────────────────────────────────┤
│  StateGraph │ CompiledGraph │ OverAllState │ RunnableConfig     │
├──────────────────────────────────────────────────────────────────┤
│                     Persistence Layer                            │
├──────────────────────────────────────────────────────────────────┤
│ PostgreSQL │ MySQL │ Oracle │ MongoDB │ Redis │ File            │
└──────────────────────────────────────────────────────────────────┘
```

## 2. 类继承关系

### 2.1 Agent 继承体系

```
                    Agent (abstract)
                         │
           ┌─────────────┴─────────────┐
           │                           │
      BaseAgent (abstract)        FlowAgent (abstract)
           │                           │
           │                 ┌─────────┼─────────┬─────────────┐
           │                 │         │         │             │
      ReactAgent    SequentialAgent ParallelAgent LoopAgent  SupervisorAgent
                                                         │
                                                    LlmRoutingAgent
```

### 2.2 Hook 继承体系

```
                    Hook (interface)
                         │
           ┌─────────────┼─────────────┐
           │             │             │
      AgentHook     ModelHook    ToolInjection
           │             │
    HumanInTheLoopHook  SummarizationHook
    InterruptionHook    ModelCallLimitHook
    MessagesModelHook   ...
```

### 2.3 Interceptor 继承体系

```
                    Interceptor (interface)
                         │
           ┌─────────────┴─────────────┐
           │                           │
     ModelInterceptor            ToolInterceptor
           │                           │
    ModelFallbackInterceptor    ToolRetryInterceptor
    ModelRetryInterceptor       ToolSelectionInterceptor
    ...                         ToolEmulatorInterceptor
```

## 3. 组件交互流程

### 3.1 ReactAgent 执行流程

```
┌──────────────────────────────────────────────────────────────────┐
│                        ReactAgent Execution                       │
└──────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│  1. buildMessageInput()                                          │
│     - 转换输入为 Message 列表                                      │
│     - 构建 inputs Map                                             │
└──────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│  2. getAndCompileGraph()                                         │
│     - initGraph(): 构建 StateGraph                                │
│     - 添加 LlmNode 和 ToolNode                                    │
│     - 编译为 CompiledGraph                                        │
└──────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│  3. compiledGraph.invoke()/stream()                              │
│     - 执行图节点                                                   │
│     - 应用 Hooks 和 Interceptors                                  │
└──────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│  4. Return OverAllState / Flux<NodeOutput>                       │
└──────────────────────────────────────────────────────────────────┘
```

### 3.2 SequentialAgent 执行流程

```
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│  START   │───▶│  Agent1  │───▶│  Agent2  │───▶│   END    │
└──────────┘    └──────────┘    └──────────┘    └──────────┘
                     │               │
                     ▼               ▼
               state["output1"]  state["output2"]
```

### 3.3 ParallelAgent 执行流程

```
                     ┌──────────┐
                     │  START   │
                     └────┬─────┘
                          │
          ┌───────────────┼───────────────┐
          │               │               │
          ▼               ▼               ▼
    ┌──────────┐   ┌──────────┐   ┌──────────┐
    │  Agent1  │   │  Agent2  │   │  Agent3  │
    └────┬─────┘   └────┬─────┘   └────┬─────┘
         │              │              │
         ▼              ▼              ▼
    output1         output2        output3
         │              │              │
         └──────────────┼──────────────┘
                        │
                        ▼
                 ┌──────────┐
                 │  Merge   │
                 └────┬─────┘
                      │
                      ▼
                 ┌──────────┐
                 │   END    │
                 └──────────┘
```

### 3.4 SupervisorAgent 执行流程

```
┌──────────┐     ┌──────────────┐     ┌──────────────────┐
│  START   │────▶│  MainAgent   │────▶│ Route Decision   │
└──────────┘     └──────────────┘     └────────┬─────────┘
                                               │
                    ┌──────────────────────────┼──────────────────────┐
                    │                          │                      │
                    ▼                          ▼                      ▼
              ┌──────────┐              ┌──────────┐           ┌──────────┐
              │ SubAgent1│              │ SubAgent2│           │  FINISH  │
              └────┬─────┘              └────┬─────┘           └────┬─────┘
                   │                         │                      │
                   └─────────────┬───────────┘                      │
                                 │                                  │
                                 ▼                                  ▼
                         ┌──────────────┐                    ┌──────────┐
                         │  MainAgent   │                    │   END    │
                         └──────────────┘                    └──────────┘
```

## 4. 状态管理

### 4.1 OverAllState

```java
// 状态结构
{
    "messages": [UserMessage, AssistantMessage, ...],
    "input": "用户输入文本",
    "article": AssistantMessage,      // Agent 输出
    "reviewed_article": AssistantMessage,
    // ... 其他自定义状态
}
```

### 4.2 状态键约定

| 键名 | 说明 |
|------|------|
| `messages` | 消息历史列表 |
| `input` | 当前用户输入 |
| `{outputKey}` | Agent 输出结果 |
| `supervisor_next` | Supervisor 下一跳决策 |

## 5. Hook 拦截点

### 5.1 Hook 位置说明

```
┌─────────────────────────────────────────────────────────────────┐
│                        Agent Execution                           │
└─────────────────────────────────────────────────────────────────┘
         │                                    │
         ▼                                    ▼
┌─────────────────┐                  ┌─────────────────┐
│   PRE_MODEL     │                  │   POST_MODEL    │
│   (模型调用前)   │─── Model Call ──▶│   (模型调用后)   │
└─────────────────┘                  └─────────────────┘
         │                                    │
         │         ┌──────────────────────────┤
         │         │                          │
         ▼         ▼                          ▼
┌─────────────────┐                  ┌─────────────────┐
│   PRE_TOOL      │                  │   POST_TOOL     │
│   (工具调用前)   │─── Tool Call ───▶│   (工具调用后)   │
└─────────────────┘                  └─────────────────┘
```

### 5.2 Hook 执行顺序

Hooks 按 `Prioritized` 接口的优先级排序执行：
- 优先级数值越小，越先执行
- 同优先级按注册顺序执行

## 6. 图构建策略

### 6.1 FlowGraphBuildingStrategy

```java
public interface FlowGraphBuildingStrategy {
    StateGraph buildGraph(FlowGraphBuilder.FlowGraphConfig config);
}
```

### 6.2 策略注册

```java
// FlowGraphBuildingStrategyRegistry
SEQUENTIAL  -> SequentialGraphBuildingStrategy
PARALLEL    -> ParallelGraphBuildingStrategy
LOOP        -> LoopGraphBuildingStrategy
ROUTING     -> RoutingGraphBuildingStrategy
SUPERVISOR  -> SupervisorGraphBuildingStrategy
CONDITIONAL -> ConditionalGraphBuildingStrategy
```

## 7. 持久化机制

### 7.1 CheckpointSaver 接口

```java
public interface CheckpointSaver {
    void put(String threadId, Checkpoint checkpoint);
    Optional<Checkpoint> get(String threadId);
    void delete(String threadId);
}
```

### 7.2 内置实现

| 实现类 | 存储介质 |
|--------|----------|
| `MemorySaver` | 内存 |
| `PostgresSaver` | PostgreSQL |
| `MongoSaver` | MongoDB |
| `RedisSaver` | Redis |
| `FileSaver` | 文件系统 |

## 8. 流式输出设计

### 8.1 OutputType 枚举

```java
public enum OutputType {
    AGENT_MODEL_STREAMING,   // Agent 模型流式输出
    AGENT_TOOL_FINISHED,     // Agent 工具执行完成
    // ... 其他类型
}
```

### 8.2 StreamingOutput

```java
public class StreamingOutput<T> implements NodeOutput {
    private final OutputType outputType;
    private final Message message;
    private final OverAllState state;
    private final TokenUsage tokenUsage;
    private final String agent;
}
```

### 8.3 流式输出过滤

Agent 基类提供 `extractMessages` 方法，只暴露用户相关的消息类型：

```java
private Flux<Message> extractMessages(Flux<NodeOutput> stream) {
    return stream.filter(o -> o instanceof StreamingOutput<?> so
            && isMessageOutputType(so.getOutputType())
            && so.message() != null)
        .map(o -> ((StreamingOutput<?>) o).message());
}
```
