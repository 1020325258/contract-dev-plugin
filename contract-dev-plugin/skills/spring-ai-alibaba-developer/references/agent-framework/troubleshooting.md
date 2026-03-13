# Spring AI Alibaba Agent Framework - 故障排查

## 1. 常见问题及解决方案

### 1.1 Agent 构建失败

**问题**: `IllegalArgumentException: Name must be provided`

**原因**: Agent 未设置 name 属性

**解决方案**:
```java
// 错误示例
ReactAgent agent = ReactAgent.builder()
    .model(chatModel)
    .build();  // 缺少 name

// 正确示例
ReactAgent agent = ReactAgent.builder()
    .name("my_agent")  // 必须设置 name
    .model(chatModel)
    .build();
```

---

**问题**: `IllegalArgumentException: At least one sub-agent must be provided for flow`

**原因**: FlowAgent (SequentialAgent, ParallelAgent 等) 未提供子 Agent

**解决方案**:
```java
// 错误示例
SequentialAgent agent = SequentialAgent.builder()
    .name("seq_agent")
    .build();  // 缺少 subAgents

// 正确示例
SequentialAgent agent = SequentialAgent.builder()
    .name("seq_agent")
    .subAgents(List.of(agent1, agent2))  // 必须提供子 Agent
    .build();
```

---

**问题**: `IllegalArgumentException: mainAgent (ReactAgent) must be provided for supervisor agent`

**原因**: SupervisorAgent 未设置 mainAgent

**解决方案**:
```java
SupervisorAgent agent = SupervisorAgent.builder()
    .name("supervisor")
    .mainAgent(mainAgent)  // 必须设置 mainAgent
    .subAgents(List.of(agent1, agent2))
    .build();
```

---

### 1.2 执行时错误

**问题**: `GraphRunnerException: Graph execution failed`

**常见原因及解决方案**:

1. **模型调用失败**
   ```java
   // 检查 ChatModel 配置
   DashScopeApi dashScopeApi = DashScopeApi.builder()
       .apiKey(System.getenv("AI_DASHSCOPE_API_KEY"))  // 确认环境变量已设置
       .build();
   ```

2. **工具调用异常**
   ```java
   // 添加工具执行拦截器捕获异常
   ToolErrorInterceptor errorInterceptor = ToolErrorInterceptor.builder()
       .onError((context, error) -> {
           log.error("Tool {} failed: {}", context.toolName(), error.getMessage());
           return "Tool execution failed: " + error.getMessage();
       })
       .build();
   ```

---

**问题**: `CompletionException` 或异步执行失败

**解决方案**:
```java
try {
    Optional<OverAllState> result = agent.invoke("input");
} catch (CompletionException e) {
    // 解析真实异常
    Throwable cause = e.getCause();
    if (cause instanceof GraphRunnerException) {
        log.error("Graph execution error", cause);
    } else if (cause instanceof AgentException) {
        log.error("Agent error", cause);
    } else {
        log.error("Unknown error", cause);
    }
}
```

---

### 1.3 状态相关问题

**问题**: `state.value("output_key")` 返回空

**可能原因**:

1. outputKey 设置错误
   ```java
   // 检查 outputKey 是否正确
   ReactAgent agent = ReactAgent.builder()
       .outputKey("article")  // 确保与访问时使用的 key 一致
       .build();

   // 访问时
   state.value("article");  // 而不是 state.value("output")
   ```

2. Agent 未执行完成
   ```java
   // 使用流式输出时，确保等待完成
   List<NodeOutput> outputs = new ArrayList<>();
   agent.stream("input")
       .doOnNext(outputs::add)
       .blockLast();  // 确保等待完成

   OverAllState finalState = outputs.get(outputs.size() - 1).state();
   ```

---

**问题**: 状态过大导致内存问题

**解决方案**:
```java
// 1. 使用状态压缩 Hook
SummarizationHook hook = SummarizationHook.builder()
    .maxTokens(2000)
    .build();

// 2. 限制消息历史
MessagesModelHook messagesHook = MessagesModelHook.builder()
    .maxMessages(10)
    .build();

// 3. 不保留完整的上下文
ReactAgent agent = ReactAgent.builder()
    .includeContents(false)
    .build();
```

---

### 1.4 工具调用问题

**问题**: 工具未被调用

**排查步骤**:
1. 检查工具是否正确注册
   ```java
   ReactAgent agent = ReactAgent.builder()
       .tools(List.of(tool1, tool2))  // 确认工具已添加
       .build();
   ```

2. 检查工具描述是否清晰
   ```java
   // 工具描述应该清晰说明用途
   @Tool(description = "获取指定城市的当前天气信息，包括温度、湿度、风速等")
   public String getWeather(
       @ToolParam(description = "城市名称，如：北京、上海") String city
   ) { ... }
   ```

3. 检查 instruction 是否引导使用工具
   ```java
   ReactAgent agent = ReactAgent.builder()
       .instruction("你有天气查询工具，当用户询问天气时，请使用 get_weather 工具")
       .tools(List.of(weatherTool))
       .build();
   ```

---

**问题**: 工具调用无限循环

**原因**: 模型持续调用工具而无法给出最终回答

**解决方案**:
```java
// 添加工具调用次数限制
ToolCallLimitHook limitHook = ToolCallLimitHook.builder()
    .maxCalls(10)
    .build();

ReactAgent agent = ReactAgent.builder()
    .hooks(List.of(limitHook))
    .build();
```

---

### 1.5 Hook 和 Interceptor 问题

**问题**: Hook 未被执行

**排查步骤**:

1. 检查 HookPosition 是否正确
   ```java
   @HookPositions({HookPosition.BEFORE_MODEL, HookPosition.AFTER_MODEL})
   public class MyModelHook extends ModelHook {
       // ...
   }
   ```

2. 检查 Hook 是否正确注册
   ```java
   ReactAgent agent = ReactAgent.builder()
       .hooks(List.of(myHook))  // 确认 Hook 已添加
       .build();
   ```

3. 检查优先级顺序
   ```java
   @Override
   public int getOrder() {
       return 100;  // 数值越小优先级越高
   }
   ```

---

**问题**: Interceptor 链执行顺序错误

**解决方案**:
```java
// Interceptor 按 order() 返回值排序执行
public class FirstInterceptor implements ModelInterceptor {
    @Override
    public int order() {
        return 1;  // 先执行
    }
}

public class SecondInterceptor implements ModelInterceptor {
    @Override
    public int order() {
        return 2;  // 后执行
    }
}
```

---

## 2. 错误信息解读

### 2.1 常见异常类型

| 异常类型 | 说明 | 处理建议 |
|---------|------|---------|
| `AgentException` | Agent 执行异常 | 检查 Agent 配置和业务逻辑 |
| `GraphStateException` | 图状态异常 | 检查 StateGraph 构建过程 |
| `GraphRunnerException` | 图执行异常 | 检查执行流程和节点配置 |
| `ModelCallLimitExceededException` | 模型调用超限 | 增加调用限制或优化逻辑 |
| `PIIDetectionException` | PII 检测异常 | 检查敏感信息处理配置 |

### 2.2 日志级别解读

```
DEBUG: 详细的执行流程信息，用于调试
INFO:   正常的执行节点切换
WARN:   潜在问题（如状态值为空、达到限制等）
ERROR:  执行失败、异常信息
```

---

## 3. 调试技巧

### 3.1 启用详细日志

```java
// 方式一: Agent 级别日志
ReactAgent agent = ReactAgent.builder()
    .name("debug_agent")
    .enableLogging(true)
    .build();

// 方式二: 自定义日志 Hook
public class DebugHook extends AgentHook {
    @Override
    public String getName() { return "debug_hook"; }

    @Override
    public CompletableFuture<Map<String, Object>> beforeAgent(OverAllState state, RunnableConfig config) {
        log.info("=== Agent State Before ===");
        log.info("Messages count: {}", state.messages().size());
        log.info("State keys: {}", state.data().keySet());
        return CompletableFuture.completedFuture(Map.of());
    }
}
```

### 3.2 检查图结构

```java
// 打印 StateGraph 结构
StateGraph graph = agent.getGraph();
System.out.println("Nodes: " + graph.getNodeNames());
System.out.println("Edges: " + graph.getEdges());
```

### 3.3 跟踪执行流程

```java
// 使用流式输出跟踪每一步
agent.stream("input")
    .doOnNext(output -> {
        System.out.println("Node: " + output.node());
        System.out.println("State changes: " + output.state().data());
    })
    .blockLast();
```

### 3.4 检查状态快照

```java
// 获取当前状态快照
RunnableConfig config = RunnableConfig.builder()
    .threadId("debug-thread")
    .build();

StateSnapshot snapshot = agent.getCurrentState(config);
System.out.println("Current state: " + snapshot.state());
```

---

## 4. 已知限制

### 4.1 并发限制

| 限制项 | 说明 | 建议 |
|-------|------|------|
| ParallelAgent 子 Agent 数量 | 建议 2-10 个 | 使用 `maxConcurrency` 控制并发 |
| LoopAgent 最大循环次数 | 默认 1000 次 | 自定义 LoopStrategy 设置更合理的限制 |
| 工具调用次数 | 无默认限制 | 使用 `ToolCallLimitHook` 限制 |

### 4.2 状态大小限制

- 状态数据存储在内存中，过大的状态会影响性能
- 持久化存储对单个状态值有大小限制（取决于具体存储实现）
- 消息历史会持续增长，需要定期压缩或清理

### 4.3 A2A 限制

- `A2aRemoteAgent` 不支持 `schedule()` 方法
- 远程 Agent 调用需要网络连接稳定
- AgentCard 信息需要与远程 Agent 实际能力匹配

---

## 5. 性能问题排查

### 5.1 执行速度慢

**可能原因**:
1. 模型调用耗时 - 检查模型响应时间
2. 工具执行耗时 - 使用异步工具
3. 状态过大 - 使用状态压缩
4. 并发不足 - 增加 `maxConcurrency`

**排查方法**:
```java
// 添加执行时间统计 Hook
public class TimingHook extends AgentHook {
    private long startTime;

    @Override
    public String getName() { return "timing_hook"; }

    @Override
    public CompletableFuture<Map<String, Object>> beforeAgent(OverAllState state, RunnableConfig config) {
        startTime = System.currentTimeMillis();
        return CompletableFuture.completedFuture(Map.of());
    }

    @Override
    public CompletableFuture<Map<String, Object>> afterAgent(OverAllState state, RunnableConfig config) {
        long duration = System.currentTimeMillis() - startTime;
        log.info("Agent {} executed in {} ms", getAgentName(), duration);
        return CompletableFuture.completedFuture(Map.of());
    }
}
```

### 5.2 内存占用高

**排查方法**:
```java
// 检查消息历史大小
int totalChars = state.messages().stream()
    .mapToInt(m -> m.getText().length())
    .sum();
System.out.println("Total message characters: " + totalChars);

// 检查状态数据大小
state.data().forEach((key, value) -> {
    if (value instanceof String) {
        System.out.println(key + ": " + ((String) value).length() + " chars");
    }
});
```

### 5.3 Token 消耗过多

**解决方案**:
```java
// 使用 TokenCounter 监控
TokenCounter counter = new TokenCounter();

// 执行后检查
System.out.println("Input tokens: " + counter.getInputTokens());
System.out.println("Output tokens: " + counter.getOutputTokens());
System.out.println("Total tokens: " + counter.getTotalTokens());
```
