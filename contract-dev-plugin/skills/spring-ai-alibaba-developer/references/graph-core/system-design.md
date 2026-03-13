# Graph Core 系统设计

## 1. 执行引擎设计

### 1.1 执行架构概览

Graph Core 的执行引擎采用**响应式编程模型**，基于 Project Reactor 实现非阻塞的流式执行。

```
┌─────────────────────────────────────────────────────────────┐
│                    用户调用层                                 │
│  invoke() / stream() / streamSnapshots()                    │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                    CompiledGraph                             │
│  - 创建 GraphRunner                                          │
│  - 管理执行配置                                               │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                    GraphRunner                               │
│  - 初始化 GraphRunnerContext                                │
│  - 委托给 MainGraphExecutor                                  │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                    MainGraphExecutor                         │
│  - 处理 START/END 节点                                       │
│  - 处理中断和恢复                                             │
│  - 委托给 NodeExecutor                                       │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                    NodeExecutor                              │
│  - 执行节点动作                                               │
│  - 更新状态                                                   │
│  - 确定下一个节点                                             │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 GraphRunner 响应式执行器

```java
public class GraphRunner {

    private final CompiledGraph compiledGraph;
    private final RunnableConfig config;
    private final AtomicReference<Object> resultValue = new AtomicReference<>();
    private final MainGraphExecutor mainGraphExecutor;

    public Flux<GraphResponse<NodeOutput>> run(OverAllState initialState) {
        return Flux.defer(() -> {
            try {
                GraphRunnerContext context = new GraphRunnerContext(
                    initialState, config, compiledGraph);
                return mainGraphExecutor.execute(context, resultValue);
            }
            catch (Exception e) {
                return Flux.error(e);
            }
        });
    }
}
```

**设计要点：**
- **Flux.defer()**: 延迟创建 Flux，支持多次订阅
- **AtomicReference**: 线程安全的结果存储
- **委托模式**: 将执行逻辑委托给 MainGraphExecutor

### 1.3 GraphRunnerContext 执行上下文

```java
public class GraphRunnerContext {

    // 执行状态
    private OverAllState currentState;
    private String currentNodeId;
    private String nextNodeId;

    // 执行控制
    private int iteration = 0;
    private boolean stop = false;

    // 配置
    private final RunnableConfig config;
    private final CompiledGraph compiledGraph;

    // 核心方法
    public Command getEntryPoint() throws Exception;
    public Command nextNodeId(String nodeId, Map<String, Object> state) throws Exception;
    public Optional<Checkpoint> addCheckpoint(String nodeId, String nextNodeId);
    public OverAllState cloneState(Map<String, Object> data);

    // 中断检查
    public boolean shouldInterrupt();
    public boolean isMaxIterationsReached();
    public boolean shouldStop();
}
```

### 1.4 MainGraphExecutor 主执行器

```java
public class MainGraphExecutor extends BaseGraphExecutor {

    private final NodeExecutor nodeExecutor;

    @Override
    public Flux<GraphResponse<NodeOutput>> execute(
            GraphRunnerContext context,
            AtomicReference<Object> resultValue) {

        // 1. 检查终止条件
        if (context.shouldStop() || context.isMaxIterationsReached()) {
            return handleCompletion(context, resultValue);
        }

        // 2. 处理从子图返回
        final var returnFromEmbed = context.getReturnFromEmbedAndReset();
        if (returnFromEmbed.isPresent()) {
            // 处理中断元数据...
            return Flux.just(GraphResponse.done(...));
        }

        // 3. 处理恢复场景
        if (context.getCurrentNodeId() != null &&
            context.getConfig().isInterrupted(context.getCurrentNodeId())) {
            context.getConfig().withNodeResumed(context.getCurrentNodeId());
            return Flux.just(GraphResponse.done(...));
        }

        // 4. 处理 START 节点
        if (context.isStartNode()) {
            return handleStartNode(context);
        }

        // 5. 处理 END 节点
        if (context.isEndNode()) {
            return handleEndNode(context, resultValue);
        }

        // 6. 处理中断
        if (context.shouldInterrupt()) {
            InterruptionMetadata metadata = InterruptionMetadata.builder(...)
                .build();
            return Flux.just(GraphResponse.done(metadata));
        }

        // 7. 委托给 NodeExecutor
        return nodeExecutor.execute(context, resultValue);
    }
}
```

### 1.5 执行流程图

```
START
  │
  ▼
┌─────────────────────────┐
│  检查终止条件            │
│  - shouldStop          │
│  - isMaxIterationsReached │
└───────────┬─────────────┘
            │ No
            ▼
┌─────────────────────────┐
│  确定当前节点            │
│  - getEntryPoint       │
│  - nextNodeId          │
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│  检查中断点              │
│  - interruptsBefore    │
│  - interruptsAfter     │
└───────────┬─────────────┘
            │ No
            ▼
┌─────────────────────────┐
│  执行节点动作            │
│  - NodeExecutor        │
│  - 更新状态             │
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│  保存 Checkpoint        │
│  - addCheckpoint       │
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│  确定下一个节点          │
│  - 固定边              │
│  - 条件边              │
└───────────┬─────────────┘
            │
            ▼
        ┌───┴───┐
        │ END?  │
        └───┬───┘
     No ─────┼───── Yes
      │      │      │
      │      │      ▼
      │      │  ┌─────────┐
      │      │  │ 完成执行 │
      │      │  └─────────┘
      │      │
      └──────┼────────────┐
             │            │
             └────────────┘
               (循环执行)
```

---

## 2. 持久化机制

### 2.1 持久化流程

```
┌─────────────────────────────────────────────────────────────┐
│                      节点执行完成                            │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                    创建 Checkpoint                           │
│  - nodeId: 当前节点                                          │
│  - nextNodeId: 下一个节点                                    │
│  - state: 状态快照                                           │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                    序列化状态                                │
│  - StateSerializer.cloneObject()                            │
│  - 深拷贝状态数据                                            │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                    调用 Saver.put()                          │
│  - 存储到指定后端                                            │
│  - 返回更新后的 RunnableConfig                               │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 MemorySaver 实现

```java
public class MemorySaver implements BaseCheckpointSaver {

    // 线程安全的存储结构
    protected final ConcurrentHashMap<String, LinkedList<Checkpoint>> map = new ConcurrentHashMap<>();

    @Override
    public Collection<Checkpoint> list(RunnableConfig config) {
        String threadId = getThreadId(config);
        return map.getOrDefault(threadId, new LinkedList<>());
    }

    @Override
    public Optional<Checkpoint> get(RunnableConfig config) {
        String threadId = getThreadId(config);
        LinkedList<Checkpoint> checkpoints = map.get(threadId);
        return (checkpoints == null || checkpoints.isEmpty())
            ? Optional.empty()
            : Optional.of(checkpoints.peek());
    }

    @Override
    public RunnableConfig put(RunnableConfig config, Checkpoint checkpoint) throws Exception {
        String threadId = getThreadId(config);
        map.computeIfAbsent(threadId, k -> new LinkedList<>()).push(checkpoint);

        return RunnableConfig.builder(config)
            .checkPointId(checkpoint.getId())
            .build();
    }

    @Override
    public Tag release(RunnableConfig config) throws Exception {
        String threadId = getThreadId(config);
        LinkedList<Checkpoint> checkpoints = map.remove(threadId);
        return new Tag(threadId, checkpoints);
    }

    protected String getThreadId(RunnableConfig config) {
        return config.getThread_id() != null
            ? config.getThread_id()
            : THREAD_ID_DEFAULT;
    }
}
```

### 2.3 PostgresSaver 实现

```java
public class PostgresSaver extends MemorySaver {

    private final PGPoolingDataSource dataSource;
    private final StateSerializer stateSerializer;

    @Override
    public RunnableConfig put(RunnableConfig config, Checkpoint checkpoint) throws Exception {
        // 1. 先存入内存
        super.put(config, checkpoint);

        // 2. 再持久化到数据库
        try (Connection conn = dataSource.getConnection()) {
            // 插入或更新线程记录
            upsertThread(conn, config.getThread_id());

            // 插入检查点记录
            insertCheckpoint(conn, config, checkpoint);
        }

        return RunnableConfig.builder(config)
            .checkPointId(checkpoint.getId())
            .build();
    }

    private void insertCheckpoint(Connection conn, RunnableConfig config, Checkpoint cp)
            throws Exception {
        String sql = """
            INSERT INTO GraphCheckpoint
            (checkpoint_id, thread_id, node_id, next_node_id, state_data, state_content_type)
            VALUES (?, ?, ?, ?, ?::jsonb, ?)
            """;
        try (PreparedStatement ps = conn.prepareStatement(sql)) {
            ps.setString(1, cp.getId());
            ps.setString(2, config.getThread_id());
            ps.setString(3, cp.getNodeId());
            ps.setString(4, cp.getNextNodeId());
            ps.setString(5, serializeState(cp.getState()));
            ps.setString(6, "application/json");
            ps.executeUpdate();
        }
    }
}
```

### 2.4 状态恢复机制

```java
// 从 Checkpoint 恢复执行
public Optional<OverAllState> invoke(OverAllState overAllState, RunnableConfig config) {
    return Optional.ofNullable(
        streamFromInitialNode(overAllState, config)
            .last()
            .map(NodeOutput::state)
            .block()
    );
}

// 获取初始状态
public Map<String, Object> getInitialState(Map<String, Object> inputs, RunnableConfig config) {
    return compileConfig.checkpointSaver()
        .flatMap(saver -> saver.get(config))
        .map(cp -> OverAllState.updateState(cp.getState(), inputs, keyStrategyMap))
        .orElseGet(() -> OverAllState.updateState(new HashMap<>(), inputs, keyStrategyMap));
}

// 恢复执行流程
public Optional<OverAllState> resume(RunnableConfig config) {
    // 1. 获取最新检查点
    Optional<Checkpoint> checkpoint = compileConfig.checkpointSaver().get().get(config);

    if (checkpoint.isEmpty()) {
        return Optional.empty();
    }

    // 2. 恢复状态
    OverAllState state = stateGraph.getStateFactory()
        .apply(checkpoint.get().getState());

    // 3. 设置恢复点
    RunnableConfig resumeConfig = RunnableConfig.builder(config)
        .nextNode(checkpoint.get().getNextNodeId())
        .build();

    // 4. 继续执行
    return invoke(state, resumeConfig);
}
```

---

## 3. 条件路由实现

### 3.1 条件边数据结构

```java
// EdgeCondition - 条件边配置
public class EdgeCondition {
    private final AsyncCommandAction singleAction;      // 单目标动作
    private final AsyncMultiCommandAction multiAction;  // 多目标动作
    private final Map<String, String> mappings;         // 路由映射表

    // 判断是否为多命令模式
    public boolean isMultiCommand() {
        return multiAction != null;
    }

    // 创建单命令条件
    public static EdgeCondition single(AsyncCommandAction action, Map<String, String> mappings) {
        return new EdgeCondition(action, null, mappings);
    }

    // 创建多命令条件
    public static EdgeCondition multi(AsyncMultiCommandAction action, Map<String, String> mappings) {
        return new EdgeCondition(null, action, mappings);
    }
}
```

### 3.2 Command 对象

```java
// Command - 节点跳转和状态更新指令
public record Command(
    String gotoNode,                    // 目标节点
    Map<String, Object> update          // 状态更新
) {
    public Command(String gotoNode) {
        this(gotoNode, Map.of());
    }

    public Command(Map<String, Object> update) {
        this(null, update);
    }
}
```

### 3.3 条件路由执行流程

```java
// 确定下一个节点
private Command nextNodeId(EdgeValue route, Map<String, Object> state,
        String nodeId, RunnableConfig config) throws Exception {

    if (route == null) {
        throw RunnableErrors.missingEdge.exception(nodeId);
    }

    // 固定目标节点
    if (route.id() != null) {
        return new Command(route.id(), state);
    }

    // 条件路由
    if (route.value() != null) {
        OverAllState derefState = stateGraph.getStateFactory().apply(state);
        EdgeCondition edgeCondition = route.value();

        // 多命令模式（并行执行）
        if (edgeCondition.isMultiCommand()) {
            String conditionalParallelNodeId = ParallelNode.formatNodeId(nodeId);
            return new Command(conditionalParallelNodeId, state);
        }
        // 单命令模式
        else {
            var singleAction = edgeCondition.singleAction();
            var command = singleAction.apply(derefState, config).get();

            // 从映射表查找目标节点
            String result = route.value().mappings().get(command.gotoNode());
            if (result == null) {
                throw RunnableErrors.missingNodeInEdgeMapping.exception(nodeId, command.gotoNode());
            }

            // 更新状态
            var currentState = OverAllState.updateState(state, command.update(), keyStrategyMap);
            return new Command(result, currentState);
        }
    }

    throw RunnableErrors.executionError.exception("invalid edge value");
}
```

### 3.4 条件路由示例

```java
// 定义条件路由
StateGraph graph = new StateGraph()
    .addNode("start", (state) -> CompletableFuture.completedFuture(Map.of()))
    .addNode("processA", processAAction)
    .addNode("processB", processBAction)
    .addNode("processC", processCAction)
    .addEdge(StateGraph.START, "start")
    .addConditionalEdges("start",
        // 条件判断函数
        (state, config) -> {
            String type = state.value("type", "default");
            return CompletableFuture.completedFuture(new Command(type));
        },
        // 路由映射
        Map.of(
            "typeA", "processA",
            "typeB", "processB",
            "default", "processC"
        )
    )
    .addEdge("processA", StateGraph.END)
    .addEdge("processB", StateGraph.END)
    .addEdge("processC", StateGraph.END);

CompiledGraph compiled = graph.compile();
```

---

## 4. 并行执行实现

### 4.1 ParallelNode 并行节点

```java
public class ParallelNode extends Node {

    public static String PARALLEL_PREFIX = "__parallel__";

    private final String sourceNodeId;
    private final String targetNodeId;
    private final List<AsyncNodeActionWithConfig> actions;
    private final List<String> actionNodeIds;
    private final Map<String, KeyStrategy> keyStrategyMap;
    private final CompileConfig compileConfig;

    public ParallelNode(
            String sourceNodeId,
            String targetNodeId,
            List<AsyncNodeActionWithConfig> actions,
            List<String> actionNodeIds,
            Map<String, KeyStrategy> keyStrategyMap,
            CompileConfig compileConfig) {

        super(formatNodeId(sourceNodeId), null);
        this.sourceNodeId = sourceNodeId;
        this.targetNodeId = targetNodeId;
        this.actions = actions;
        this.actionNodeIds = actionNodeIds;
        this.keyStrategyMap = keyStrategyMap;
        this.compileConfig = compileConfig;
    }

    public static String formatNodeId(String sourceNodeId) {
        return PARALLEL_PREFIX + sourceNodeId;
    }

    @Override
    public ActionFactory actionFactory() {
        return (config) -> (state, runnableConfig) -> {
            // 并行执行所有分支
            List<CompletableFuture<Map<String, Object>>> futures = actions.stream()
                .map(action -> action.apply(state, runnableConfig))
                .toList();

            // 等待所有分支完成
            CompletableFuture<Void> allOf = CompletableFuture.allOf(
                futures.toArray(new CompletableFuture[0]));

            // 合并结果
            return allOf.thenApply(v -> {
                Map<String, Object> mergedState = new HashMap<>(state.data());
                for (CompletableFuture<Map<String, Object>> future : futures) {
                    Map<String, Object> partialState = future.join();
                    OverAllState.updateState(mergedState, partialState, keyStrategyMap);
                }
                return mergedState;
            });
        };
    }
}
```

### 4.2 ConditionalParallelNode 条件并行节点

```java
public class ConditionalParallelNode extends Node {

    private final String sourceNodeId;
    private final EdgeCondition edgeCondition;
    private final Map<String, Node.ActionFactory> nodeFactories;
    private final Map<String, KeyStrategy> keyStrategyMap;
    private final CompileConfig compileConfig;

    @Override
    public ActionFactory actionFactory() {
        return (config) -> (state, runnableConfig) -> {
            // 1. 执行条件判断获取目标列表
            AsyncMultiCommandAction multiAction = edgeCondition.multiAction();
            List<String> targetKeys = multiAction.apply(state, runnableConfig).get();

            // 2. 映射到实际节点 ID
            List<String> targetNodeIds = targetKeys.stream()
                .map(key -> edgeCondition.mappings().get(key))
                .filter(Objects::nonNull)
                .toList();

            // 3. 创建并执行节点动作
            List<CompletableFuture<Map<String, Object>>> futures = targetNodeIds.stream()
                .map(nodeId -> {
                    Node.ActionFactory factory = nodeFactories.get(nodeId);
                    try {
                        AsyncNodeActionWithConfig action = factory.apply(compileConfig);
                        return action.apply(state, runnableConfig);
                    } catch (Exception e) {
                        return CompletableFuture.completedFuture(Map.of());
                    }
                })
                .toList();

            // 4. 等待所有分支完成并合并结果
            CompletableFuture<Void> allOf = CompletableFuture.allOf(
                futures.toArray(new CompletableFuture[0]));

            return allOf.thenApply(v -> {
                Map<String, Object> mergedState = new HashMap<>(state.data());
                for (CompletableFuture<Map<String, Object>> future : futures) {
                    Map<String, Object> partialState = future.join();
                    OverAllState.updateState(mergedState, partialState, keyStrategyMap);
                }
                return mergedState;
            });
        };
    }
}
```

### 4.3 并行执行流程图

```
                    ┌─────────────────┐
                    │   Source Node   │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │  ParallelNode   │
                    │  (条件判断)      │
                    └────────┬────────┘
                             │
         ┌───────────────────┼───────────────────┐
         │                   │                   │
         ▼                   ▼                   ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│    Branch A     │ │    Branch B     │ │    Branch C     │
│   (并行执行)    │ │   (并行执行)    │ │   (并行执行)    │
└────────┬────────┘ └────────┬────────┘ └────────┬────────┘
         │                   │                   │
         └───────────────────┼───────────────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │  状态合并       │
                    │  (KeyStrategy)  │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │   Target Node   │
                    └─────────────────┘
```

### 4.4 并行执行示例

```java
// 定义并行执行
StateGraph graph = new StateGraph()
    .addNode("start", startAction)
    .addNode("analyze", analyzeAction)
    .addNode("transform", transformAction)
    .addNode("validate", validateAction)
    .addNode("aggregate", aggregateAction)
    .addEdge(StateGraph.START, "start")

    // 并行边：从 start 同时执行 analyze、transform、validate
    .addEdge("start", List.of("analyze", "transform", "validate"))

    // 所有分支完成后汇聚到 aggregate
    .addEdge(List.of("analyze", "transform", "validate"), "aggregate")
    .addEdge("aggregate", StateGraph.END);

// 或者使用条件并行
graph.addParallelConditionalEdges("start",
    (state, config) -> {
        // 根据状态决定并行执行哪些分支
        List<String> branches = new ArrayList<>();
        if (state.value("needAnalyze", true)) branches.add("analyze");
        if (state.value("needTransform", true)) branches.add("transform");
        if (state.value("needValidate", true)) branches.add("validate");
        return CompletableFuture.completedFuture(branches);
    },
    Map.of(
        "analyze", "analyze",
        "transform", "transform",
        "validate", "validate"
    )
);
```

---

## 5. 中断与恢复机制

### 5.1 Human-in-the-loop 设计

```java
// 配置中断点
CompileConfig config = CompileConfig.builder()
    .saverConfig(saverConfig)
    .interruptsBefore(List.of("humanReview"))   // 在 humanReview 前中断
    .interruptsAfter(List.of("dataProcess"))    // 在 dataProcess 后中断
    .build();

CompiledGraph compiled = graph.compile(config);
```

### 5.2 InterruptableAction 接口

```java
public interface InterruptableAction extends AsyncNodeActionWithConfig {

    // 执行前是否中断
    default boolean interruptBefore() {
        return false;
    }

    // 执行后是否中断
    default boolean interruptAfter() {
        return false;
    }
}
```

### 5.3 中断执行流程

```java
// MainGraphExecutor 中断处理
if (context.shouldInterrupt()) {
    try {
        InterruptionMetadata metadata = InterruptionMetadata
            .builder(context.getCurrentNodeId(), context.cloneState(context.getCurrentStateData()))
            .build();
        return Flux.just(GraphResponse.done(metadata));
    }
    catch (Exception e) {
        return Flux.just(GraphResponse.error(e));
    }
}
```

### 5.4 恢复执行

```java
// 恢复中断的执行
RunnableConfig config = RunnableConfig.builder()
    .thread_id("thread-123")
    .checkPointId("cp-456")
    .build();

// 获取中断状态
StateSnapshot snapshot = compiled.getState(config);

// 更新状态（人工审批后）
RunnableConfig newConfig = compiled.updateState(config, Map.of(
    "approved", true,
    "reviewComment", "Approved by reviewer"
));

// 继续执行
Optional<OverAllState> result = compiled.invoke(null, newConfig);
```

---

## 6. 生命周期监听

### 6.1 GraphLifecycleListener 接口

```java
public interface GraphLifecycleListener {

    String EXECUTION_ID_KEY = "executionId";

    // 图开始
    void onStart(RunnableConfig config, OverAllState state);

    // 图结束
    void onEnd(RunnableConfig config, OverAllState state);

    // 错误发生
    void onError(RunnableConfig config, OverAllState state, Exception e);

    // 节点开始
    void onNodeStart(String nodeId, RunnableConfig config, OverAllState state);

    // 节点结束
    void onNodeEnd(String nodeId, RunnableConfig config, OverAllState state);
}
```

### 6.2 配置监听器

```java
// 自定义监听器
public class LoggingLifecycleListener implements GraphLifecycleListener {
    private static final Logger log = LoggerFactory.getLogger(LoggingLifecycleListener.class);

    @Override
    public void onStart(RunnableConfig config, OverAllState state) {
        log.info("Graph started: threadId={}", config.getThread_id());
    }

    @Override
    public void onNodeEnd(String nodeId, RunnableConfig config, OverAllState state) {
        log.info("Node completed: nodeId={}, state={}", nodeId, state.data());
    }

    @Override
    public void onEnd(RunnableConfig config, OverAllState state) {
        log.info("Graph completed: threadId={}", config.getThread_id());
    }
}

// 注册监听器
CompileConfig config = CompileConfig.builder()
    .saverConfig(saverConfig)
    .lifecycleListeners(List.of(new LoggingLifecycleListener()))
    .build();
```

---

## 7. 子图嵌套

### 7.1 子图节点类型

| 类型 | 类 | 说明 |
|------|------|------|
| 未编译子图 | `SubStateGraphNode` | 在父图编译时一并编译 |
| 已编译子图 | `SubCompiledGraphNode` | 使用已编译的 CompiledGraph |

### 7.2 子图使用示例

```java
// 定义子图
StateGraph subGraph = new StateGraph()
    .addNode("subTaskA", taskAAction)
    .addNode("subTaskB", taskBAction)
    .addEdge(StateGraph.START, "subTaskA")
    .addEdge("subTaskA", "subTaskB")
    .addEdge("subTaskB", StateGraph.END);

// 添加子图到主图
StateGraph mainGraph = new StateGraph()
    .addNode("prepare", prepareAction)
    .addNode("subProcess", subGraph)  // 添加子图节点
    .addNode("finalize", finalizeAction)
    .addEdge(StateGraph.START, "prepare")
    .addEdge("prepare", "subProcess")
    .addEdge("subProcess", "finalize")
    .addEdge("finalize", StateGraph.END);
```

### 7.3 子图状态共享

子图与父图共享同一个 `OverAllState`，状态更新会自动合并。

```java
// 子图更新状态
AsyncNodeAction taskAAction = (state) -> {
    // 读取父图状态
    String context = state.value("context", "");

    // 更新状态（会合并到父图状态）
    return CompletableFuture.completedFuture(Map.of(
        "subResult", "processed: " + context
    ));
};
```
