# Graph Core 故障排查指南

本文档提供 Spring AI Alibaba Graph Core 的常见问题排查指南，帮助开发者快速定位和解决问题。

## 1. 常见错误及解决方案

### 1.1 图编译错误

#### 错误：缺失入口点 (Missing Entry Point)

**错误信息：**
```
GraphStateException: missing entry point
```

**原因：** 图没有定义从 START 到第一个节点的边。

**解决方案：**
```java
// 错误：缺少 START 边
StateGraph graph = new StateGraph()
    .addNode("process", processAction)
    .addEdge("process", StateGraph.END);

// 正确：添加 START 边
StateGraph graph = new StateGraph()
    .addNode("process", processAction)
    .addEdge(StateGraph.START, "process")  // 添加入口点
    .addEdge("process", StateGraph.END);
```

---

#### 错误：无效节点标识符 (Invalid Node Identifier)

**错误信息：**
```
GraphStateException: invalid node identifier: __myNode
```

**原因：** 节点 ID 以 `__` 开头，这是系统保留前缀。

**解决方案：**
```java
// 错误：使用保留前缀
graph.addNode("__myNode", action);

// 正确：使用合法的节点 ID
graph.addNode("myNode", action);
```

---

#### 错误：重复节点 (Duplicate Node)

**错误信息：**
```
GraphStateException: duplicate node error: processNode
```

**原因：** 尝试添加同名节点。

**解决方案：**
```java
// 错误：重复添加同名节点
graph.addNode("process", action1);
graph.addNode("process", action2);  // 错误！

// 正确：使用不同的节点 ID
graph.addNode("process1", action1);
graph.addNode("process2", action2);
```

---

#### 错误：边引用缺失节点 (Missing Node Referenced by Edge)

**错误信息：**
```
GraphStateException: missing node referenced by edge: targetNode
```

**原因：** 边的目标节点不存在。

**解决方案：**
```java
// 错误：边引用不存在的节点
graph.addNode("source", sourceAction)
    .addEdge("source", "nonExistentTarget");  // 错误！

// 正确：先添加节点，再添加边
graph.addNode("source", sourceAction)
    .addNode("target", targetAction)
    .addEdge("source", "target");
```

---

### 1.2 执行时错误

#### 错误：缺失边 (Missing Edge)

**错误信息：**
```
RunnableException: missing edge for node: processNode
```

**原因：** 节点执行完成后没有定义下一个节点。

**解决方案：**
```java
// 错误：节点没有出边
graph.addNode("process", processAction);
// 缺少 process 的出边

// 正确：为每个节点定义出边
graph.addNode("process", processAction)
    .addEdge("process", StateGraph.END);  // 或其他节点
```

---

#### 错误：边映射中缺失节点 (Missing Node in Edge Mapping)

**错误信息：**
```
RunnableException: missing node in edge mapping for node 'router' with key 'unknownKey'
```

**原因：** 条件路由返回的键在映射表中不存在。

**解决方案：**
```java
// 错误：条件返回值不在映射表中
graph.addConditionalEdges("router",
    (state, config) -> CompletableFuture.completedFuture(new Command("unknownKey")),
    Map.of("keyA", "nodeA", "keyB", "nodeB")  // 缺少 unknownKey
);

// 正确：提供所有可能的映射，包括默认值
graph.addConditionalEdges("router",
    (state, config) -> CompletableFuture.completedFuture(new Command("keyA")),
    Map.of("keyA", "nodeA", "keyB", "nodeB", "default", "defaultNode")
);
```

---

#### 错误：达到最大迭代次数 (Max Iterations Reached)

**错误信息：**
```
Graph stopped: max iterations reached (25)
```

**原因：** 图执行超过了配置的递归限制（默认 25）。

**可能原因：**
1. 图中存在无限循环
2. 递归限制设置过低

**解决方案：**
```java
// 方案一：修复无限循环
// 检查条件路由是否正确终止

// 方案二：增加递归限制
CompileConfig config = CompileConfig.builder()
    .recursionLimit(100)  // 增加限制
    .build();

CompiledGraph compiled = graph.compile(config);
```

---

### 1.3 持久化错误

#### 错误：缺失 CheckpointSaver (Missing CheckpointSaver)

**错误信息：**
```
IllegalStateException: Missing CheckpointSaver!
```

**原因：** 尝试使用状态恢复功能但没有配置持久化器。

**解决方案：**
```java
// 错误：没有配置 Saver
CompiledGraph compiled = graph.compile();
compiled.getState(config);  // 错误！

// 正确：配置 Saver
SaverConfig saverConfig = SaverConfig.builder()
    .register(new MemorySaver())
    .build();

CompileConfig config = CompileConfig.builder()
    .saverConfig(saverConfig)
    .build();

CompiledGraph compiled = graph.compile(config);
```

---

#### 错误：缺失 Checkpoint (Missing Checkpoint)

**错误信息：**
```
IllegalStateException: Missing Checkpoint!
```

**原因：** 尝试恢复一个不存在的检查点。

**解决方案：**
```java
// 错误：线程 ID 对应的检查点不存在
RunnableConfig config = RunnableConfig.builder()
    .threadId("non-existent-thread")
    .build();
compiled.getState(config);  // 错误！

// 正确：先检查检查点是否存在
Optional<StateSnapshot> snapshot = compiled.stateOf(config);
if (snapshot.isPresent()) {
    // 恢复执行
} else {
    // 新建执行
}
```

---

#### 错误：数据库连接失败

**错误信息：**
```
SQLException: Connection refused
PSQLException: FATAL: database "graph_db" does not exist
```

**原因：** 数据库连接配置错误或数据库不存在。

**解决方案：**
```java
// 检查数据库配置
PostgresSaver saver = PostgresSaver.builder()
    .host("localhost")
    .port(5432)
    .database("graph_db")
    .user("postgres")
    .password("password")
    .createTables(true)  // 自动创建表
    .build();

// 确保数据库存在
// CREATE DATABASE graph_db;
```

---

### 1.4 序列化错误

#### 错误：序列化失败

**错误信息：**
```
IOException: Serialization failed
JsonProcessingException: Cannot serialize object
```

**原因：** 状态中包含不可序列化的对象。

**解决方案：**
```java
// 错误：存储不可序列化的对象
Map<String, Object> state = Map.of(
    "connection", databaseConnection,  // 不可序列化
    "stream", inputStream             // 不可序列化
);

// 正确：只存储可序列化的数据
Map<String, Object> state = Map.of(
    "connectionId", "conn-123",  // 只存 ID
    "data", "serialized string"   // 可序列化
);
```

---

## 2. 调试技巧

### 2.1 使用生命周期监听器

```java
public class DebugListener implements GraphLifecycleListener {
    private static final Logger log = LoggerFactory.getLogger(DebugListener.class);

    @Override
    public void onStart(RunnableConfig config, OverAllState state) {
        log.info("=== Graph Started ===");
        log.info("Thread ID: {}", config.getThread_id());
        log.info("Initial State: {}", state.data());
    }

    @Override
    public void before(String nodeId, RunnableConfig config, OverAllState state, long startTime) {
        log.info(">>> Node Starting: {}", nodeId);
        log.debug("Current State: {}", state.data());
    }

    @Override
    public void after(String nodeId, RunnableConfig config, OverAllState state, long endTime) {
        log.info("<<< Node Completed: {}", nodeId);
        log.debug("Updated State: {}", state.data());
    }

    @Override
    public void onError(RunnableConfig config, OverAllState state, Exception e) {
        log.error("!!! Graph Error !!!");
        log.error("Thread ID: {}", config.getThread_id());
        log.error("State at Error: {}", state.data(), e);
    }

    @Override
    public void onEnd(RunnableConfig config, OverAllState state) {
        log.info("=== Graph Completed ===");
        log.info("Final State: {}", state.data());
    }
}

// 注册监听器
CompileConfig config = CompileConfig.builder()
    .lifecycleListeners(List.of(new DebugListener()))
    .build();
```

### 2.2 图可视化

```java
// 生成图的可视化表示
CompiledGraph compiled = graph.compile();

// Mermaid 格式
GraphRepresentation mermaid = compiled.getGraph(GraphRepresentation.Type.MERMAID);
System.out.println(mermaid.content());

// 检查图结构是否正确
```

### 2.3 查看执行历史

```java
// 获取执行历史
Collection<StateSnapshot> history = compiled.getStateHistory(config);

System.out.println("=== Execution History ===");
for (StateSnapshot snapshot : history) {
    System.out.println("Node: " + snapshot.getNodeId());
    System.out.println("Next: " + snapshot.getNextNodeId());
    System.out.println("State: " + snapshot.getState().data());
    System.out.println("---");
}
```

### 2.4 节点输出调试

```java
// 使用流式执行查看每个节点的输出
Flux<NodeOutput> stream = compiled.stream(inputs, config);

stream.doOnNext(output -> {
    System.out.println("Node: " + output.node());
    System.out.println("State: " + output.state());
    System.out.println("---");
}).blockLast();
```

---

## 3. 已知限制

### 3.1 状态大小限制

| 存储后端 | 建议单条状态大小 | 说明 |
|----------|------------------|------|
| MemorySaver | 无限制 | 受 JVM 内存限制 |
| FileSystemSaver | 100MB | 文件系统限制 |
| PostgresSaver | 1GB (JSONB) | PostgreSQL JSONB 限制 |
| RedisSaver | 512MB | Redis 字符串限制 |

### 3.2 并发限制

- `OverAllState` 不是线程安全的
- 并行节点数建议不超过 CPU 核心数
- 并发执行时需要外部同步状态访问

### 3.3 递归深度限制

- 默认递归限制：25 次
- 最大建议值：100 次
- 超过限制会导致执行终止

### 3.4 子图限制

- 子图深度建议不超过 3 层
- 子图与父图共享状态，注意状态污染

---

## 4. 性能问题排查

### 4.1 执行缓慢

**排查步骤：**

1. **检查节点执行时间**
```java
public class TimingListener implements GraphLifecycleListener {
    private final Map<String, Long> startTimes = new ConcurrentHashMap<>();

    @Override
    public void before(String nodeId, RunnableConfig config, OverAllState state, long startTime) {
        startTimes.put(nodeId, startTime);
    }

    @Override
    public void after(String nodeId, RunnableConfig config, OverAllState state, long endTime) {
        long duration = endTime - startTimes.get(nodeId);
        System.out.println("Node " + nodeId + " took " + duration + "ms");
    }
}
```

2. **检查状态大小**
```java
// 在节点中打印状态大小
graph.addNode("debug", (state) -> {
    System.out.println("State size: " + estimateSize(state.data()) + " bytes");
    return CompletableFuture.completedFuture(Map.of());
});
```

3. **检查并行效率**
```java
// 检查并行节点是否真正并行执行
// 查看线程池配置
```

### 4.2 内存溢出

**排查步骤：**

1. **检查状态累积**
```java
// 检查 AppendStrategy 字段是否无限增长
List<?> messages = state.value("messages", new ArrayList<>());
System.out.println("Messages count: " + messages.size());
```

2. **检查检查点累积**
```java
Collection<StateSnapshot> history = compiled.getStateHistory(config);
System.out.println("Checkpoint count: " + history.size());
```

3. **解决方案：定期清理**
```java
// 清理状态
graph.addNode("cleanup", (state) -> {
    List<Message> messages = state.value("messages", new ArrayList<>());
    if (messages.size() > 100) {
        return CompletableFuture.completedFuture(Map.of(
            "messages", messages.subList(messages.size() - 50, messages.size())
        ));
    }
    return CompletableFuture.completedFuture(Map.of());
});
```

### 4.3 数据库性能问题

**排查步骤：**

1. **检查索引**
```sql
-- PostgreSQL
CREATE INDEX idx_checkpoint_thread ON GraphCheckpoint(thread_id);
CREATE INDEX idx_checkpoint_created ON GraphCheckpoint(saved_at);
```

2. **检查连接池**
```java
// 配置连接池
PostgresSaver saver = PostgresSaver.builder()
    .host("localhost")
    .port(5432)
    .database("graph_db")
    .maxPoolSize(20)  // 连接池大小
    .build();
```

---

## 5. 错误信息速查表

| 错误类型 | 错误信息 | 原因 | 解决方案 |
|----------|----------|------|----------|
| 编译错误 | missing entry point | 缺少 START 边 | 添加 `addEdge(START, firstNode)` |
| 编译错误 | invalid node identifier | 节点 ID 以 `__` 开头 | 使用合法的节点 ID |
| 编译错误 | duplicate node error | 重复的节点 ID | 使用唯一的节点 ID |
| 编译错误 | missing node referenced by edge | 边引用不存在的节点 | 先添加节点再添加边 |
| 执行错误 | missing edge for node | 节点没有出边 | 添加节点的出边 |
| 执行错误 | missing node in edge mapping | 条件路由键不存在 | 添加所有可能的映射 |
| 执行错误 | max iterations reached | 超过递归限制 | 修复循环或增加限制 |
| 持久化错误 | Missing CheckpointSaver | 未配置持久化 | 配置 SaverConfig |
| 持久化错误 | Missing Checkpoint | 检查点不存在 | 先执行或检查线程 ID |
| 序列化错误 | Serialization failed | 不可序列化对象 | 只存基本类型 |

---

## 6. 常见问题 FAQ

### Q1: 如何恢复中断的执行？

```java
// 1. 获取中断状态
RunnableConfig config = RunnableConfig.builder()
    .threadId("interrupted-thread")
    .build();

StateSnapshot snapshot = compiled.getState(config);

// 2. 更新状态（如人工审批结果）
RunnableConfig updatedConfig = compiled.updateState(config, Map.of(
    "approved", true,
    "reviewComment", "Approved"
));

// 3. 恢复执行
Optional<OverAllState> result = compiled.invoke(null, updatedConfig);
```

### Q2: 如何处理并行分支的错误？

```java
// 方案一：分支内部处理错误
graph.addNode("branchA", (state) -> {
    try {
        return CompletableFuture.completedFuture(Map.of("resultA", process()));
    } catch (Exception e) {
        return CompletableFuture.completedFuture(Map.of("errorA", e.getMessage()));
    }
});

// 方案二：汇聚节点检查错误
graph.addNode("merge", (state) -> {
    String errorA = state.value("errorA", "");
    String errorB = state.value("errorB", "");

    if (!errorA.isEmpty() || !errorB.isEmpty()) {
        return CompletableFuture.completedFuture(Map.of(
            "status", "partial_failure",
            "errors", List.of(errorA, errorB)
        ));
    }
    return CompletableFuture.completedFuture(Map.of("status", "success"));
});
```

### Q3: 如何调试条件路由？

```java
// 添加调试节点
graph.addNode("debugRouter", (state, config) -> {
    String decision = makeDecision(state);

    // 打印路由决策
    System.out.println("Routing decision: " + decision);
    System.out.println("State: " + state.data());

    return CompletableFuture.completedFuture(Map.of());
});

// 在条件路由前添加调试
graph.addEdge(StateGraph.START, "debugRouter")
    .addConditionalEdges("debugRouter", condition, mappings);
```

### Q4: 如何查看图的执行轨迹？

```java
// 方式一：使用流式执行
Flux<NodeOutput> stream = compiled.stream(inputs);
stream.doOnNext(output -> {
    System.out.println("Visited: " + output.node());
}).blockLast();

// 方式二：使用生命周期监听器
// 见 2.1 节

// 方式三：查看状态历史
Collection<StateSnapshot> history = compiled.getStateHistory(config);
```

### Q5: 如何处理大状态？

```java
// 方案一：使用 Store 存储大数据
Store store = new MemoryStore();  // 或其他实现

CompileConfig config = CompileConfig.builder()
    .store(store)
    .build();

// 在节点中存储大对象
graph.addNode("process", (state) -> {
    String dataId = UUID.randomUUID().toString();
    state.getStore().putItem(StoreItem.of(
        List.of("largeData"),
        dataId,
        largeDataMap
    ));

    // 状态中只存 ID
    return CompletableFuture.completedFuture(Map.of("dataId", dataId));
});

// 方案二：定期清理
// 见 4.2 节
```

---

## 7. 联系支持

如果以上方法无法解决您的问题，可以：

1. 查看项目 GitHub Issues: https://github.com/alibaba/spring-ai-alibaba/issues
2. 查阅完整文档
3. 提交新的 Issue，包含：
   - 错误信息和堆栈跟踪
   - 复现步骤
   - 相关代码片段
   - 环境信息（JDK 版本、Spring Boot 版本等）
