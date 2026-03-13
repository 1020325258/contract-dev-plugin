# Graph Core 最佳实践

本文档提供 Spring AI Alibaba Graph Core 的最佳实践指南，帮助开发者避免常见陷阱并构建高性能、可维护的工作流应用。

## 1. 状态设计最佳实践

### 1.1 状态字段规划

**推荐做法：**

```java
// 好：明确的状态字段规划，清晰的合并策略
KeyStrategyFactory factory = KeyStrategyFactoryBuilder.builder()
    // 对话历史：追加模式
    .withKey("messages", new AppendStrategy())
    // 当前处理结果：替换模式
    .withKey("currentResult", new ReplaceStrategy())
    // 用户配置：合并模式
    .withKey("config", new MergeStrategy())
    // 错误信息：追加模式
    .withKey("errors", new AppendStrategy())
    .build();
```

**避免做法：**

```java
// 差：没有规划状态结构，全部使用默认替换
StateGraph graph = new StateGraph(); // 所有字段默认 ReplaceStrategy

// 差：过度嵌套的状态结构
Map<String, Object> nested = Map.of(
    "level1", Map.of(
        "level2", Map.of(
            "level3", Map.of(
                "data", "value"
            )
        )
    )
);
```

### 1.2 状态字段命名规范

| 字段类型 | 命名建议 | 合并策略 |
|----------|----------|----------|
| 对话消息 | `messages`, `history` | `AppendStrategy` |
| 处理结果 | `result`, `output` | `ReplaceStrategy` |
| 配置信息 | `config`, `settings` | `MergeStrategy` |
| 错误信息 | `errors`, `logs` | `AppendStrategy` |
| 临时数据 | `temp_*`, `cache_*` | `ReplaceStrategy` |
| 元数据 | `metadata`, `context` | `MergeStrategy` |

### 1.3 状态大小控制

**推荐做法：**

```java
// 好：定期清理不必要的状态字段
graph.addNode("cleanup", (state) -> {
    Map<String, Object> updates = new HashMap<>();

    // 清理临时数据
    updates.put("temp_data", OverAllState.MARK_FOR_REMOVAL);

    // 限制历史长度
    List<Message> messages = state.value("messages", new ArrayList<>());
    if (messages.size() > 100) {
        updates.put("messages", messages.subList(messages.size() - 50, messages.size()));
    }

    return CompletableFuture.completedFuture(updates);
});
```

**避免做法：**

```java
// 差：状态无限增长
graph.addNode("process", (state) -> {
    // 每次都添加大量数据，从不清理
    return CompletableFuture.completedFuture(Map.of(
        "allData", getAllHistoricalData() // 数据量随时间无限增长
    ));
});
```

---

## 2. 图结构设计最佳实践

### 2.1 单一职责原则

**推荐做法：**

```java
// 好：每个节点职责单一
graph.addNode("validateInput", (state) -> {
    // 只做输入验证
    String input = state.value("input", "");
    if (input.isEmpty()) {
        return CompletableFuture.completedFuture(Map.of(
            "error", "Input cannot be empty"
        ));
    }
    return CompletableFuture.completedFuture(Map.of(
        "validated", true
    ));
});

graph.addNode("transformData", (state) -> {
    // 只做数据转换
    String input = state.value("input", "");
    return CompletableFuture.completedFuture(Map.of(
        "transformed", input.toUpperCase()
    ));
});

graph.addNode("saveResult", (state) -> {
    // 只做结果保存
    String data = state.value("transformed", "");
    saveToDatabase(data);
    return CompletableFuture.completedFuture(Map.of(
        "saved", true
    ));
});
```

**避免做法：**

```java
// 差：一个节点做太多事情
graph.addNode("doEverything", (state) -> {
    // 验证、转换、保存都在一个节点
    String input = state.value("input", "");
    if (input.isEmpty()) throw new Exception("empty");
    String transformed = input.toUpperCase();
    saveToDatabase(transformed);
    sendNotification(transformed);
    logResult(transformed);
    // ... 职责过多
    return CompletableFuture.completedFuture(Map.of("done", true));
});
```

### 2.2 图深度控制

**推荐做法：**

```java
// 好：使用子图管理复杂逻辑
StateGraph subGraph = new StateGraph()
    .addNode("step1", step1Action)
    .addNode("step2", step2Action)
    .addNode("step3", step3Action)
    .addEdge(StateGraph.START, "step1")
    .addEdge("step1", "step2")
    .addEdge("step2", "step3")
    .addEdge("step3", StateGraph.END);

StateGraph mainGraph = new StateGraph()
    .addNode("prepare", prepareAction)
    .addNode("process", subGraph)  // 复杂逻辑封装为子图
    .addNode("finalize", finalizeAction)
    .addEdge(StateGraph.START, "prepare")
    .addEdge("prepare", "process")
    .addEdge("process", "finalize")
    .addEdge("finalize", StateGraph.END);
```

**避免做法：**

```java
// 差：过于扁平的深度链
graph.addNode("step1", ...)
    .addNode("step2", ...)
    .addNode("step3", ...)
    // ... 20+ 个节点的线性链
    .addNode("step20", ...);
```

### 2.3 条件路由设计

**推荐做法：**

```java
// 好：清晰的路由逻辑和默认分支
graph.addConditionalEdges("router",
    (state, config) -> {
        String type = state.value("type", "default");
        // 明确的返回值
        return CompletableFuture.completedFuture(new Command(type));
    },
    Map.of(
        "typeA", "processA",
        "typeB", "processB",
        "default", "defaultProcess"  // 总是提供默认分支
    )
);
```

**避免做法：**

```java
// 差：复杂的路由逻辑，没有默认分支
graph.addConditionalEdges("router",
    (state, config) -> {
        // 复杂的条件判断
        if (condition1 && condition2 || condition3) {
            return CompletableFuture.completedFuture(new Command("A"));
        } else if (...) {
            // 嵌套的条件判断
        }
        // 可能没有匹配的分支，导致错误
    },
    Map.of("A", "processA", "B", "processB")  // 缺少默认分支
);
```

---

## 3. 并行执行最佳实践

### 3.1 并行分支设计

**推荐做法：**

```java
// 好：独立的并行分支，状态合并清晰
KeyStrategyFactory factory = KeyStrategyFactoryBuilder.builder()
    .withKey("analysisResult", new ReplaceStrategy())
    .withKey("reportData", new ReplaceStrategy())
    .withKey("notifications", new AppendStrategy())
    .build();

StateGraph graph = new StateGraph(factory)
    .addNode("start", startAction)
    .addNode("analyze", (state) -> {
        // 独立的分析逻辑
        return CompletableFuture.completedFuture(Map.of(
            "analysisResult", analyzeData()
        ));
    })
    .addNode("report", (state) -> {
        // 独立的报告逻辑
        return CompletableFuture.completedFuture(Map.of(
            "reportData", generateReport()
        ));
    })
    .addNode("notify", (state) -> {
        // 独立的通知逻辑
        return CompletableFuture.completedFuture(Map.of(
            "notifications", List.of("Processing started")
        ));
    })
    .addEdge("start", List.of("analyze", "report", "notify"));
```

**避免做法：**

```java
// 差：并行分支有数据竞争
graph.addNode("branchA", (state) -> {
    // 修改同一个状态字段
    return CompletableFuture.completedFuture(Map.of(
        "result", "A"  // 与 branchB 冲突
    ));
});
graph.addNode("branchB", (state) -> {
    return CompletableFuture.completedFuture(Map.of(
        "result", "B"  // 与 branchA 冲突
    ));
});
graph.addEdge("start", List.of("branchA", "branchB"));
```

### 3.2 并发控制

**推荐做法：**

```java
// 好：通过配置控制并发度
RunnableConfig config = RunnableConfig.builder()
    .threadId("concurrent-execution")
    .addMetadata("__MAX_CONCURRENCY__parallelNode", 3)  // 限制并发数
    .build();

compiled.invoke(inputs, config);
```

---

## 4. 持久化最佳实践

### 4.1 存储后端选择

| 场景 | 推荐存储 | 理由 |
|------|----------|------|
| 开发测试 | `MemorySaver` | 无需配置，快速迭代 |
| 单机生产 | `FileSystemSaver` | 简单可靠，易于备份 |
| 分布式生产 | `PostgresSaver` / `MysqlSaver` | 支持集群，事务安全 |
| 高性能场景 | `RedisSaver` | 内存存储，低延迟 |
| 文档型数据 | `MongoSaver` | 灵活 Schema，JSON 原生支持 |

### 4.2 检查点清理策略

**推荐做法：**

```java
// 好：定期清理历史检查点
public class CheckpointCleanupListener implements GraphLifecycleListener {
    @Override
    public void onEnd(RunnableConfig config, OverAllState state) {
        // 保留最近 10 个检查点
        Collection<StateSnapshot> history = compiled.getStateHistory(config);
        if (history.size() > 10) {
            // 清理旧的检查点...
        }
    }
}
```

### 4.3 状态序列化注意点

**推荐做法：**

```java
// 好：使用可序列化的数据类型
Map<String, Object> state = Map.of(
    "name", "test",           // String
    "count", 100,             // Integer
    "data", List.of(1, 2, 3), // List
    "config", Map.of("key", "value")  // Map
);

// 差：使用不可序列化的对象
Map<String, Object> badState = Map.of(
    "connection", databaseConnection,  // 不可序列化
    "thread", Thread.currentThread(),  // 不可序列化
    "stream", inputStream             // 不可序列化
);
```

---

## 5. 错误处理最佳实践

### 5.1 节点级错误处理

**推荐做法：**

```java
// 好：节点内部处理错误，返回状态
graph.addNode("riskyOperation", (state) -> {
    try {
        String result = performOperation();
        return CompletableFuture.completedFuture(Map.of(
            "result", result,
            "success", true
        ));
    } catch (BusinessException e) {
        return CompletableFuture.completedFuture(Map.of(
            "error", e.getMessage(),
            "success", false,
            "retryable", e.isRetryable()
        ));
    }
});

// 后续节点根据状态决定流程
graph.addConditionalEdges("riskyOperation",
    (state, config) -> {
        Boolean success = state.value("success", false);
        return CompletableFuture.completedFuture(
            new Command(success ? "continue" : "errorHandler")
        );
    },
    Map.of("continue", "nextStep", "errorHandler", "handleError")
);
```

**避免做法：**

```java
// 差：直接抛出异常
graph.addNode("riskyOperation", (state) -> {
    String result = performOperation();  // 可能抛出异常
    return CompletableFuture.completedFuture(Map.of("result", result));
    // 异常会中断整个图执行
});
```

### 5.2 全局错误处理

**推荐做法：**

```java
// 好：使用生命周期监听器记录错误
public class ErrorLoggingListener implements GraphLifecycleListener {
    private static final Logger log = LoggerFactory.getLogger(ErrorLoggingListener.class);

    @Override
    public void onError(RunnableConfig config, OverAllState state, Exception e) {
        log.error("Graph execution error: threadId={}, state={}",
            config.getThread_id(), state.data(), e);

        // 发送告警
        alertService.notify(e);
    }
}

CompileConfig config = CompileConfig.builder()
    .lifecycleListeners(List.of(new ErrorLoggingListener()))
    .build();
```

---

## 6. 性能优化建议

### 6.1 状态优化

| 优化点 | 建议 |
|--------|------|
| 状态大小 | 单个状态字段不超过 1MB |
| 状态字段数 | 控制在 20 个以内 |
| 历史数据 | 定期清理，使用 Store 存储长期数据 |
| 大对象 | 使用引用 ID，不直接存储 |

### 6.2 执行优化

```java
// 好：使用流式执行处理大数据
Flux<NodeOutput> stream = compiled.stream(inputs, config);
stream.buffer(10)  // 批量处理
    .subscribe(batch -> processBatch(batch));

// 好：并行执行独立任务
graph.addEdge("fork", List.of("taskA", "taskB", "taskC"));
```

### 6.3 内存优化

```java
// 好：及时清理不需要的状态
graph.addNode("cleanup", (state) -> {
    return CompletableFuture.completedFuture(Map.of(
        "largeTempData", OverAllState.MARK_FOR_REMOVAL
    ));
});
```

---

## 7. 安全考虑

### 7.1 输入验证

**推荐做法：**

```java
// 好：在入口节点验证输入
graph.addNode("validateInput", (state) -> {
    String input = state.value("input", "");

    // 验证输入
    if (input.length() > 10000) {
        return CompletableFuture.completedFuture(Map.of(
            "error", "Input too large"
        ));
    }

    if (containsMaliciousContent(input)) {
        return CompletableFuture.completedFuture(Map.of(
            "error", "Invalid input"
        ));
    }

    return CompletableFuture.completedFuture(Map.of("validated", true));
});
```

### 7.2 敏感数据处理

**推荐做法：**

```java
// 好：敏感数据不存入状态
graph.addNode("processPayment", (state) -> {
    // 从安全存储获取敏感数据
    String creditCard = secureStorage.getCreditCard(state.value("userId"));

    // 处理后立即清除
    String result = processPayment(creditCard);
    creditCard = null;  // 清除引用

    // 只存储非敏感结果
    return CompletableFuture.completedFuture(Map.of(
        "paymentStatus", result
    ));
});

// 差：敏感数据存入状态
graph.addNode("badExample", (state) -> {
    return CompletableFuture.completedFuture(Map.of(
        "creditCard", "1234-5678-9012-3456"  // 危险！
    ));
});
```

### 7.3 并发安全

```java
// 注意：OverAllState 不是线程安全的
// 在并发访问时需要外部同步

public class SafeStateAccess {
    private final Object lock = new Object();

    public void safeUpdate(OverAllState state, Map<String, Object> updates) {
        synchronized (lock) {
            state.updateState(updates);
        }
    }
}
```

---

## 8. 可观测性最佳实践

### 8.1 日志记录

**推荐做法：**

```java
public class LoggingListener implements GraphLifecycleListener {
    private static final Logger log = LoggerFactory.getLogger(LoggingListener.class);

    @Override
    public void onStart(RunnableConfig config, OverAllState state) {
        log.info("Graph started: threadId={}", config.getThread_id());
    }

    @Override
    public void before(String nodeId, RunnableConfig config, OverAllState state, long startTime) {
        log.debug("Node starting: nodeId={}, threadId={}", nodeId, config.getThread_id());
    }

    @Override
    public void after(String nodeId, RunnableConfig config, OverAllState state, long endTime) {
        log.debug("Node completed: nodeId={}, threadId={}", nodeId, config.getThread_id());
    }

    @Override
    public void onError(RunnableConfig config, OverAllState state, Exception e) {
        log.error("Graph error: threadId={}", config.getThread_id(), e);
    }
}
```

### 8.2 指标收集

**推荐做法：**

```java
public class MetricsListener implements GraphLifecycleListener {
    private final MeterRegistry meterRegistry;

    @Override
    public void before(String nodeId, RunnableConfig config, OverAllState state, long startTime) {
        Timer.Sample sample = Timer.start(meterRegistry);
        // 存储 sample 用于后续记录
    }

    @Override
    public void after(String nodeId, RunnableConfig config, OverAllState state, long endTime) {
        meterRegistry.counter("graph.node.completed", "nodeId", nodeId).increment();
    }
}
```

---

## 9. 测试最佳实践

### 9.1 单元测试

```java
@Test
void testNodeExecution() throws Exception {
    // 创建测试状态
    OverAllState state = new OverAllState(Map.of("input", "test"));

    // 创建节点动作
    AsyncNodeAction action = (s) -> CompletableFuture.completedFuture(
        Map.of("result", "processed: " + s.value("input", ""))
    );

    // 执行并验证
    Map<String, Object> result = action.apply(state).get();
    assertEquals("processed: test", result.get("result"));
}

@Test
void testConditionalRouting() throws Exception {
    StateGraph graph = new StateGraph()
        .addNode("router", (state) -> CompletableFuture.completedFuture(Map.of()))
        .addNode("pathA", (state) -> CompletableFuture.completedFuture(Map.of("path", "A")))
        .addNode("pathB", (state) -> CompletableFuture.completedFuture(Map.of("path", "B")))
        .addEdge(StateGraph.START, "router")
        .addConditionalEdges("router",
            (state, config) -> CompletableFuture.completedFuture(new Command("goA")),
            Map.of("goA", "pathA", "goB", "pathB")
        )
        .addEdge("pathA", StateGraph.END)
        .addEdge("pathB", StateGraph.END);

    CompiledGraph compiled = graph.compile();
    Optional<OverAllState> result = compiled.invoke(Map.of());

    assertTrue(result.isPresent());
    assertEquals("A", result.get().value("path").orElse(""));
}
```

### 9.2 集成测试

```java
@SpringBootTest
class GraphIntegrationTest {

    @Autowired
    private DataSource dataSource;

    @Test
    void testWithPostgresPersistence() throws Exception {
        PostgresSaver saver = PostgresSaver.builder()
            .dataSource(dataSource)
            .createTables(true)
            .build();

        CompileConfig config = CompileConfig.builder()
            .saverConfig(SaverConfig.builder().register(saver).build())
            .build();

        CompiledGraph compiled = createTestGraph().compile(config);

        // 测试持久化和恢复
        RunnableConfig runConfig = RunnableConfig.builder()
            .threadId("test-thread")
            .build();

        Optional<OverAllState> result = compiled.invoke(Map.of("input", "test"), runConfig);
        assertTrue(result.isPresent());

        // 验证状态已持久化
        StateSnapshot snapshot = compiled.getState(runConfig);
        assertNotNull(snapshot);
    }
}
```

---

## 10. 反例对比总结

### 10.1 状态设计反例

| 反例 | 问题 | 正确做法 |
|------|------|----------|
| 状态无限增长 | 内存溢出风险 | 定期清理，设置上限 |
| 过度嵌套 | 难以维护 | 扁平化设计 |
| 存储不可序列化对象 | 持久化失败 | 只存基本类型 |

### 10.2 图结构反例

| 反例 | 问题 | 正确做法 |
|------|------|----------|
| 单节点多职责 | 难以测试和维护 | 单一职责 |
| 无限循环 | 资源耗尽 | 设置递归限制 |
| 深度过大 | 性能问题 | 使用子图 |

### 10.3 并行执行反例

| 反例 | 问题 | 正确做法 |
|------|------|----------|
| 并行分支写同一字段 | 数据竞争 | 使用不同字段 |
| 无并发控制 | 资源耗尽 | 限制并发数 |
| 依赖顺序的并行 | 逻辑错误 | 明确依赖关系 |

### 10.4 持久化反例

| 反例 | 问题 | 正确做法 |
|------|------|----------|
| 开发环境用 Redis | 配置复杂 | 使用 MemorySaver |
| 不清理历史检查点 | 存储膨胀 | 定期清理 |
| 存储敏感数据 | 安全风险 | 只存引用 ID |
