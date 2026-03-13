# Spring AI Alibaba Agent Framework - API 参考

## 1. Agent 基类 API

### 1.1 Agent

**包路径**: `com.alibaba.cloud.ai.graph.agent.Agent`

**核心方法**:

| 方法 | 参数 | 返回值 | 说明 |
|------|------|--------|------|
| `name()` | - | `String` | 获取 Agent 名称 |
| `description()` | - | `String` | 获取 Agent 描述 |
| `invoke(String)` | message | `Optional<OverAllState>` | 同步执行（文本输入） |
| `invoke(UserMessage)` | message | `Optional<OverAllState>` | 同步执行（UserMessage） |
| `invoke(List<Message>)` | messages | `Optional<OverAllState>` | 同步执行（消息列表） |
| `invoke(Map<String, Object>)` | inputs | `Optional<OverAllState>` | 同步执行（Map 输入） |
| `invokeAndGetOutput(...)` | ... | `Optional<NodeOutput>` | 执行并获取输出 |
| `stream(...)` | ... | `Flux<NodeOutput>` | 流式执行 |
| `streamMessages(...)` | ... | `Flux<Message>` | 流式输出消息 |
| `schedule(Trigger, Map)` | trigger, input | `ScheduledAgentTask` | 调度执行 |
| `getCurrentState(RunnableConfig)` | config | `StateSnapshot` | 获取当前状态 |

---

## 2. ReactAgent API

### 2.1 ReactAgentBuilder

**包路径**: `com.alibaba.cloud.ai.graph.agent.ReactAgent.ReactAgentBuilder`

| 方法 | 参数 | 说明 |
|------|------|------|
| `name(String)` | name | 设置 Agent 名称（必填） |
| `model(ChatModel)` | chatModel | 设置大模型（必填） |
| `description(String)` | description | 设置 Agent 描述 |
| `instruction(String)` | instruction | 设置系统指令 |
| `tools(List<ToolCallback>)` | tools | 设置工具列表 |
| `hooks(List<Hook>)` | hooks | 设置 Hooks |
| `interceptors(List<Interceptor>)` | interceptors | 设置拦截器 |
| `outputKey(String)` | outputKey | 设置输出键 |
| `outputSchema(String)` | schema | 设置输出 Schema |
| `outputType(Class<?>)` | type | 设置输出类型 |
| `saver(CheckpointSaver)` | saver | 设置状态持久化 |
| `includeContents(boolean)` | flag | 是否包含上下文 |
| `returnReasoningContents(boolean)` | flag | 是否返回推理内容 |
| `enableLogging(boolean)` | flag | 是否启用日志 |
| `build()` | - | 构建 Agent |

### 2.2 ReactAgent 方法

| 方法 | 说明 |
|------|------|
| `call(String)` | 简单调用，返回 AssistantMessage |
| `call(UserMessage)` | 简单调用，返回 AssistantMessage |
| `getOutputKey()` | 获取输出键 |
| `getInstruction()` | 获取系统指令 |

---

## 3. SequentialAgent API

### 3.1 SequentialAgentBuilder

**包路径**: `com.alibaba.cloud.ai.graph.agent.flow.agent.SequentialAgent.SequentialAgentBuilder`

| 方法 | 参数 | 说明 |
|------|------|------|
| `name(String)` | name | 设置 Agent 名称（必填） |
| `description(String)` | description | 设置 Agent 描述 |
| `subAgents(List<Agent>)` | agents | 设置子 Agent 列表（必填） |
| `stateSerializer(StateSerializer)` | serializer | 设置状态序列化器 |
| `hooks(List<Hook>)` | hooks | 设置 Hooks |
| `executor(Executor)` | executor | 设置执行器 |
| `build()` | - | 构建 Agent |

---

## 4. ParallelAgent API

### 4.1 ParallelAgentBuilder

**包路径**: `com.alibaba.cloud.ai.graph.agent.flow.agent.ParallelAgent.ParallelAgentBuilder`

| 方法 | 参数 | 说明 |
|------|------|------|
| `name(String)` | name | 设置 Agent 名称（必填） |
| `description(String)` | description | 设置 Agent 描述 |
| `subAgents(List<Agent>)` | agents | 设置子 Agent 列表（必填，2-10个） |
| `mergeStrategy(MergeStrategy)` | strategy | 设置合并策略 |
| `mergeOutputKey(String)` | key | 设置合并输出键 |
| `maxConcurrency(Integer)` | max | 设置最大并发数 |
| `build()` | - | 构建 Agent |

### 4.2 MergeStrategy 接口

**包路径**: `com.alibaba.cloud.ai.graph.agent.flow.agent.ParallelAgent.MergeStrategy`

```java
public interface MergeStrategy {
    Object merge(Map<String, Object> subAgentResults, OverAllState overallState);
}
```

**内置实现**:

| 类名 | 说明 |
|------|------|
| `DefaultMergeStrategy` | 返回包含所有结果的 Map |
| `ListMergeStrategy` | 返回结果列表 |
| `ConcatenationMergeStrategy` | 字符串拼接结果 |

---

## 5. LoopAgent API

### 5.1 LoopAgentBuilder

**包路径**: `com.alibaba.cloud.ai.graph.agent.flow.agent.LoopAgent.LoopAgentBuilder`

| 方法 | 参数 | 说明 |
|------|------|------|
| `name(String)` | name | 设置 Agent 名称（必填） |
| `description(String)` | description | 设置 Agent 描述 |
| `subAgent(Agent)` | agent | 设置子 Agent（必填） |
| `loopStrategy(LoopStrategy)` | strategy | 设置循环策略（必填） |
| `build()` | - | 构建 Agent |

### 5.2 LoopStrategy 接口

**包路径**: `com.alibaba.cloud.ai.graph.agent.flow.agent.loop.LoopStrategy`

```java
public interface LoopStrategy {
    boolean shouldContinue(OverAllState state);
    void beforeLoop(OverAllState state);
    void afterLoop(OverAllState state);
}
```

### 5.3 LoopMode 工厂方法

**包路径**: `com.alibaba.cloud.ai.graph.agent.flow.agent.loop.LoopMode`

| 方法 | 参数 | 说明 |
|------|------|------|
| `count(int)` | count | 固定次数循环 |
| `condition(Predicate<OverAllState>)` | predicate | 条件循环 |
| `array(String, String)` | arrayKey, itemKey | 数组迭代循环 |

---

## 6. SupervisorAgent API

### 6.1 SupervisorAgentBuilder

**包路径**: `com.alibaba.cloud.ai.graph.agent.flow.agent.SupervisorAgent.SupervisorAgentBuilder`

| 方法 | 参数 | 说明 |
|------|------|------|
| `name(String)` | name | 设置 Agent 名称（必填） |
| `description(String)` | description | 设置 Agent 描述 |
| `mainAgent(ReactAgent)` | agent | 设置主决策 Agent（必填） |
| `subAgents(List<Agent>)` | agents | 设置子 Agent 列表 |
| `build()` | - | 构建 Agent |

---

## 7. Hook API

### 7.1 Hook 接口

**包路径**: `com.alibaba.cloud.ai.graph.agent.hook.Hook`

```java
public interface Hook extends Prioritized {
    HookPosition position();
    Object apply(OverAllState state, AgentHook hook);
}
```

### 7.2 HookPosition

**包路径**: `com.alibaba.cloud.ai.graph.agent.hook.HookPosition`

| 枚举值 | 说明 |
|--------|------|
| `PRE_MODEL` | 模型调用前 |
| `POST_MODEL` | 模型调用后 |
| `PRE_TOOL` | 工具调用前 |
| `POST_TOOL` | 工具调用后 |

### 7.3 内置 Hook

| Hook 类 | 说明 |
|---------|------|
| `HumanInTheLoopHook` | 人机交互 |
| `SummarizationHook` | 消息摘要 |
| `ModelCallLimitHook` | 模型调用限制 |
| `ToolCallLimitHook` | 工具调用限制 |
| `PIIDetectionHook` | 敏感信息检测 |
| `InterruptionHook` | 中断处理 |
| `MessagesModelHook` | 消息处理 |

---

## 8. Interceptor API

### 8.1 Interceptor 接口

**包路径**: `com.alibaba.cloud.ai.graph.agent.interceptor.Interceptor`

```java
public interface Interceptor extends Prioritized {
    InterceptorType type();
}
```

### 8.2 ModelInterceptor

**包路径**: `com.alibaba.cloud.ai.graph.agent.interceptor.ModelInterceptor`

```java
public interface ModelInterceptor extends Interceptor {
    ModelResponse intercept(ModelRequest request, ModelCallHandler next);
}
```

### 8.3 ToolInterceptor

**包路径**: `com.alibaba.cloud.ai.graph.agent.interceptor.ToolInterceptor`

```java
public interface ToolInterceptor extends Interceptor {
    ToolCallResponse intercept(ToolCallExecutionContext context, ToolCallHandler next);
}
```

### 8.4 内置 Interceptor

| Interceptor 类 | 类型 | 说明 |
|----------------|------|------|
| `ModelFallbackInterceptor` | MODEL | 模型降级 |
| `ModelRetryInterceptor` | MODEL | 模型重试 |
| `ToolRetryInterceptor` | TOOL | 工具重试 |
| `ToolSelectionInterceptor` | TOOL | 工具选择 |
| `ToolEmulatorInterceptor` | TOOL | 工具模拟 |
| `ToolErrorInterceptor` | TOOL | 工具错误处理 |
| `ContextEditingInterceptor` | TOOL | 上下文编辑 |
| `TodoListInterceptor` | TOOL | 待办列表 |
| `SkillsInterceptor` | TOOL | 技能管理 |

---

## 9. 状态相关 API

### 9.1 OverAllState

**包路径**: `com.alibaba.cloud.ai.graph.OverAllState`

| 方法 | 返回值 | 说明 |
|------|--------|------|
| `value(String)` | `Optional<Object>` | 获取指定键的值 |
| `messages()` | `List<Message>` | 获取消息列表 |
| `data()` | `Map<String, Object>` | 获取所有数据 |

### 9.2 NodeOutput

**包路径**: `com.alibaba.cloud.ai.graph.NodeOutput`

| 方法 | 返回值 | 说明 |
|------|--------|------|
| `state()` | `OverAllState` | 获取状态 |
| `tokenUsage()` | `TokenUsage` | 获取 Token 使用量 |
| `agent()` | `String` | 获取 Agent 名称 |

### 9.3 RunnableConfig

**包路径**: `com.alibaba.cloud.ai.graph.RunnableConfig`

```java
RunnableConfig config = RunnableConfig.builder()
    .threadId("thread-123")
    .checkpointId("checkpoint-456")
    .addMetadata("key", "value")
    .build();
```

---

## 10. 工具相关 API

### 10.1 ToolCallback

**包路径**: `org.springframework.ai.tool.ToolCallback`

| 方法 | 说明 |
|------|------|
| `getName()` | 获取工具名称 |
| `getDescription()` | 获取工具描述 |
| `call(String)` | 执行工具调用 |

### 10.2 AsyncToolCallback

**包路径**: `com.alibaba.cloud.ai.graph.agent.tool.AsyncToolCallback`

```java
public interface AsyncToolCallback extends ToolCallback {
    CompletableFuture<String> callAsync(String functionInput, CancellationToken cancellationToken);
}
```

### 10.3 CancellableAsyncToolCallback

**包路径**: `com.alibaba.cloud.ai.graph.agent.tool.CancellableAsyncToolCallback`

```java
public interface CancellableAsyncToolCallback extends AsyncToolCallback {
    void cancel();
    boolean isCancelled();
}
```
