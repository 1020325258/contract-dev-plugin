# Spring AI Alibaba Agent Framework - 最佳实践

## 1. 推荐的使用模式

### 1.1 Agent 设计原则

**单一职责原则**

每个 Agent 应该只负责一个明确的任务，通过组合多个单一职责的 Agent 来实现复杂功能。

```java
// 推荐: 单一职责的 Agent
ReactAgent writerAgent = ReactAgent.builder()
    .name("writer_agent")
    .instruction("你只负责写文章，不要做其他事情")
    .outputKey("article")
    .build();

ReactAgent reviewerAgent = ReactAgent.builder()
    .name("reviewer_agent")
    .instruction("你只负责审核文章")
    .outputKey("reviewed_article")
    .build();

// 不推荐: 承担过多职责的 Agent
ReactAgent doAllAgent = ReactAgent.builder()
    .name("all_in_one")
    .instruction("你需要写文章、审核、发布...")
    .build();
```

**清晰的命名规范**

- Agent 名称使用 snake_case 格式
- 名称应该体现 Agent 的职责
- outputKey 应该语义明确

```java
// 推荐
.name("sql_generator_agent")
.outputKey("generated_sql")

// 不推荐
.name("agent1")
.outputKey("output")
```

### 1.2 编排模式选择指南

| 需求场景 | 推荐模式 | 说明 |
|---------|---------|------|
| 流水线处理 | SequentialAgent | 每个步骤依赖前一步骤输出 |
| 独立任务并行 | ParallelAgent | 多个任务无依赖关系 |
| 迭代处理 | LoopAgent | 需要重复执行直到满足条件 |
| 动态路由 | SupervisorAgent | 需要根据上下文动态选择 |
| 条件分支 | ConditionalGraph | 需要根据条件走不同分支 |

### 1.3 状态管理最佳实践

**合理使用 outputKey**

```java
// 推荐: 每个阶段有明确的 outputKey
ReactAgent step1 = ReactAgent.builder()
    .name("step1")
    .outputKey("step1_result")
    .build();

ReactAgent step2 = ReactAgent.builder()
    .name("step2")
    .instruction("处理上一步的结果: {step1_result}")
    .outputKey("step2_result")
    .build();
```

**控制上下文大小**

```java
// 推荐: 对于审核类 Agent，不需要完整上下文
ReactAgent reviewer = ReactAgent.builder()
    .name("reviewer")
    .includeContents(false)  // 不包含完整上下文
    .instruction("""
        审核以下文章:
        {article}
        """)
    .build();
```

---

## 2. 性能优化建议

### 2.1 Token 优化

**使用消息压缩 Hook**

```java
// 当对话过长时，使用摘要压缩
SummarizationHook summarizationHook = SummarizationHook.builder()
    .maxTokens(4000)
    .summarizationModel(chatModel)
    .build();

ReactAgent agent = ReactAgent.builder()
    .name("long_conversation_agent")
    .model(chatModel)
    .hooks(List.of(summarizationHook))
    .build();
```

**限制消息历史**

```java
// 限制保留的消息数量
MessagesModelHook messagesHook = MessagesModelHook.builder()
    .maxMessages(20)
    .build();
```

### 2.2 并发控制

```java
// ParallelAgent 中控制并发数
ParallelAgent parallelAgent = ParallelAgent.builder()
    .name("parallel_tasks")
    .subAgents(List.of(agent1, agent2, agent3, agent4, agent5))
    .maxConcurrency(3)  // 避免过多并发导致资源竞争
    .build();
```

### 2.3 模型调用优化

**限制模型调用次数**

```java
ModelCallLimitHook limitHook = ModelCallLimitHook.builder()
    .maxCalls(10)
    .build();

ReactAgent agent = ReactAgent.builder()
    .hooks(List.of(limitHook))
    .build();
```

**使用模型重试机制**

```java
ModelRetryInterceptor retryInterceptor = ModelRetryInterceptor.builder()
    .maxRetries(3)
    .retryDelay(Duration.ofSeconds(1))
    .build();
```

### 2.4 流式输出优化

```java
// 对于长时间任务，使用流式输出提升用户体验
agent.streamMessages("写一个长故事")
    .doOnNext(msg -> {
        // 实时展示，避免用户等待
        System.out.print(((AssistantMessage) msg).getText());
    })
    .blockLast();
```

---

## 3. 安全考虑

### 3.1 敏感信息检测

**使用 PII 检测 Hook**

```java
PIIDetectionHook piiHook = PIIDetectionHook.builder()
    .detectors(List.of(
        PIIDetectors.phone(),      // 电话号码
        PIIDetectors.email(),      // 邮箱
        PIIDetectors.idCard(),     // 身份证
        PIIDetectors.bankCard()    // 银行卡
    ))
    .redactionStrategy(RedactionStrategy.MASK)  // 脱敏处理
    .build();

ReactAgent agent = ReactAgent.builder()
    .name("secure_agent")
    .hooks(List.of(piiHook))
    .build();
```

### 3.2 工具调用安全

**限制工具调用次数**

```java
ToolCallLimitHook toolLimitHook = ToolCallLimitHook.builder()
    .maxCalls(20)
    .build();
```

**工具权限控制**

```java
// 只允许调用特定工具
ToolSelectionInterceptor selectionInterceptor = ToolSelectionInterceptor.builder()
    .allowedTools(List.of("get_weather", "search"))
    .build();
```

### 3.3 输入验证

```java
// 在 Agent 执行前验证输入
public class InputValidationHook extends AgentHook {
    @Override
    public String getName() {
        return "input_validation_hook";
    }

    @Override
    public CompletableFuture<Map<String, Object>> beforeAgent(OverAllState state, RunnableConfig config) {
        String input = state.value("input").orElse("").toString();
        if (input.length() > 10000) {
            throw new AgentException("输入过长，请限制在10000字符以内");
        }
        return CompletableFuture.completedFuture(Map.of());
    }
}
```

---

## 4. 反例对比

### 4.1 嵌套层级过深

```java
// 不推荐: 嵌套层级过深
SequentialAgent level3 = SequentialAgent.builder()
    .subAgents(List.of(agent1, agent2))
    .build();
SequentialAgent level2 = SequentialAgent.builder()
    .subAgents(List.of(level3, agent3))
    .build();
SequentialAgent level1 = SequentialAgent.builder()
    .subAgents(List.of(level2, agent4))
    .build();

// 推荐: 扁平化设计
SequentialAgent main = SequentialAgent.builder()
    .subAgents(List.of(agent1, agent2, agent3, agent4))
    .build();
```

### 4.2 忽略错误处理

```java
// 不推荐: 没有错误处理
Optional<OverAllState> result = agent.invoke("input");
String output = result.get().value("output").get().toString();

// 推荐: 完善的错误处理
try {
    Optional<OverAllState> result = agent.invoke("input");
    if (result.isEmpty()) {
        log.warn("Agent returned empty result");
        return;
    }
    Optional<Object> output = result.get().value("output");
    if (output.isEmpty()) {
        log.warn("Output key not found in state");
        return;
    }
    // 处理输出
} catch (CompletionException e) {
    log.error("Agent execution failed", e.getCause());
    // 错误恢复逻辑
}
```

### 4.3 不合理的工具设计

```java
// 不推荐: 工具描述不清晰
@Tool
public String process(String data) { ... }

// 推荐: 清晰的工具描述
@Tool(description = "处理用户数据，返回处理结果")
public String processUserData(
    @ToolParam(description = "用户数据，JSON格式") String userData
) { ... }
```

### 4.4 过度使用 ParallelAgent

```java
// 不推荐: 任务之间有依赖关系时使用并行
ParallelAgent parallelAgent = ParallelAgent.builder()
    .subAgents(List.of(writerAgent, reviewerAgent))  // reviewer 依赖 writer 的输出
    .build();

// 推荐: 使用顺序执行
SequentialAgent sequentialAgent = SequentialAgent.builder()
    .subAgents(List.of(writerAgent, reviewerAgent))
    .build();
```

---

## 5. 可观测性

### 5.1 日志配置

```java
// 启用详细日志
ReactAgent agent = ReactAgent.builder()
    .name("debug_agent")
    .enableLogging(true)
    .build();
```

### 5.2 Token 统计

```java
// 使用 TokenCounter Hook
TokenCounter tokenCounter = new TokenCounter();

ReactAgent agent = ReactAgent.builder()
    .hooks(List.of(tokenCounter))
    .build();

// 执行后获取统计
System.out.println("Total tokens: " + tokenCounter.getTotalTokens());
```

### 5.3 执行链路追踪

```java
// 自定义 Hook 记录执行链路
public class TracingHook extends AgentHook {

    @Override
    public String getName() {
        return "tracing_hook";
    }

    @Override
    public CompletableFuture<Map<String, Object>> beforeAgent(OverAllState state, RunnableConfig config) {
        String traceId = (String) config.getMetadata().getOrDefault("traceId", "unknown");
        log.info("[{}] Agent {} starting", traceId, getAgentName());
        return CompletableFuture.completedFuture(Map.of());
    }

    @Override
    public CompletableFuture<Map<String, Object>> afterAgent(OverAllState state, RunnableConfig config) {
        String traceId = (String) config.getMetadata().getOrDefault("traceId", "unknown");
        log.info("[{}] Agent {} completed", traceId, getAgentName());
        return CompletableFuture.completedFuture(Map.of());
    }
}
```

---

## 6. 测试建议

### 6.1 单元测试

```java
@Test
void testAgentOutput() throws Exception {
    // 使用 Mock 模型进行测试
    ChatModel mockModel = mock(ChatModel.class);
    when(mockModel.call(any())).thenReturn(mockResponse);

    ReactAgent agent = ReactAgent.builder()
        .name("test_agent")
        .model(mockModel)
        .build();

    Optional<OverAllState> result = agent.invoke("test input");

    assertTrue(result.isPresent());
    verify(mockModel, times(1)).call(any());
}
```

### 6.2 集成测试

```java
@SpringBootTest
class AgentIntegrationTest {

    @Autowired
    private ChatModel chatModel;

    @Test
    void testSequentialAgentFlow() {
        ReactAgent agent1 = ReactAgent.builder()
            .name("agent1")
            .model(chatModel)
            .outputKey("result1")
            .build();

        ReactAgent agent2 = ReactAgent.builder()
            .name("agent2")
            .model(chatModel)
            .instruction("处理: {result1}")
            .outputKey("result2")
            .build();

        SequentialAgent seq = SequentialAgent.builder()
            .subAgents(List.of(agent1, agent2))
            .build();

        Optional<OverAllState> result = seq.invoke("test");

        assertTrue(result.get().value("result1").isPresent());
        assertTrue(result.get().value("result2").isPresent());
    }
}
```
