# Graph Core API 参考

本文档提供 Spring AI Alibaba Graph Core 模块的核心 API 参考。

## 1. 核心类

### 1.1 StateGraph

状态图定义类，用于构建工作流图。

**包路径**: `com.alibaba.cloud.ai.graph.StateGraph`

```java
public class StateGraph {
    // 常量定义
    public static final String END = "__END__";
    public static final String START = "__START__";
    public static final String ERROR = "__ERROR__";

    // 构造方法
    public StateGraph(KeyStrategyFactory keyStrategyFactory);
    public StateGraph();

    // 节点管理
    public StateGraph addNode(String id, AsyncNodeAction action);
    public StateGraph addNode(String id, StateGraph subGraph);
    public StateGraph addNode(String id, CompiledGraph subGraph);

    // 边管理
    public StateGraph addEdge(String sourceId, String targetId);
    public StateGraph addEdge(String sourceId, List<String> targetIds);

    // 条件路由
    public StateGraph addConditionalEdges(String sourceId,
            AsyncCommandAction condition, Map<String, String> mappings);

    // 并行条件路由
    public StateGraph addParallelConditionalEdges(String sourceId,
            AsyncMultiCommandAction condition, Map<String, String> mappings);

    // 编译
    public CompiledGraph compile();
    public CompiledGraph compile(CompileConfig config);
}
```

**示例**：

```java
// 创建图
StateGraph graph = new StateGraph(keyStrategyFactory)
    .addNode("start", startAction)
    .addNode("process", processAction)
    .addEdge(StateGraph.START, "start")
    .addEdge("start", "process")
    .addEdge("process", StateGraph.END);

CompiledGraph compiled = graph.compile();
```

---

### 1.2 CompiledGraph

编译后的图，提供执行入口。

**包路径**: `com.alibaba.cloud.ai.graph.CompiledGraph`

```java
public class CompiledGraph {
    // 配置访问
    public final StateGraph stateGraph;
    public final CompileConfig compileConfig;

    // 同步执行
    public Optional<OverAllState> invoke(Map<String, Object> inputs);
    public Optional<OverAllState> invoke(Map<String, Object> inputs, RunnableConfig config);

    // 流式执行
    public Flux<NodeOutput> stream(Map<String, Object> inputs);
    public Flux<NodeOutput> stream(Map<String, Object> inputs, RunnableConfig config);

    // 快照流
    public Flux<StateSnapshot> streamSnapshots(RunnableConfig config);

    // 状态管理
    public Optional<OverAllState> getState(RunnableConfig config);
    public List<StateSnapshot> getStateHistory(RunnableConfig config);
    public RunnableConfig updateState(RunnableConfig config, Map<String, Object> values);

    // 节点访问
    public AsyncNodeActionWithConfig getNodeAction(String nodeId);
    public EdgeValue getEdge(String nodeId);
}
```

**示例**：

```java
// 同步执行
Optional<OverAllState> result = compiled.invoke(inputs);

// 流式执行
Flux<NodeOutput> stream = compiled.stream(inputs);
stream.subscribe(output -> {
    System.out.println("Node: " + output.node());
});

// 获取历史状态
List<StateSnapshot> history = compiled.getStateHistory(config);
```

---

### 1.3 OverAllState

整体状态容器。

**包路径**: `com.alibaba.cloud.ai.graph.OverAllState`

```java
public final class OverAllState implements Serializable {
    // 常量
    public static final String DEFAULT_INPUT_KEY = "input";
    public static final Object MARK_FOR_REMOVAL = new Object();

    // 状态数据访问
    public Map<String, Object> data();
    public <T> T value(String key);
    public <T> T value(String key, T defaultValue);
    public <T> Optional<T> value(TypeRef<T> typeRef);

    // 状态更新
    public void updateState(Map<String, Object> values);
    public static Map<String, Object> updateState(
        Map<String, Object> state,
        Map<String, Object> values,
        Map<String, KeyStrategy> channels);

    // 策略管理
    public void registerKeyAndStrategy(String key, KeyStrategy strategy);
    public Map<String, KeyStrategy> keyStrategies();

    // 快照
    public Optional<OverAllState> snapShot();

    // 输入处理
    public OverAllState input(Map<String, Object> input);
    public OverAllState input(Object input);
}
```

**示例**：

```java
// 在节点动作中访问状态
AsyncNodeAction action = (state) -> {
    String name = state.value("name", "default");
    List<Message> messages = state.value("messages", new ArrayList<>());

    return CompletableFuture.completedFuture(Map.of(
        "result", "processed: " + name
    ));
};
```

---

## 2. 状态策略

### 2.1 KeyStrategy

状态合并策略接口。

**包路径**: `com.alibaba.cloud.ai.graph.KeyStrategy`

```java
@FunctionalInterface
public interface KeyStrategy extends BinaryOperator<Object> {
    Object apply(Object oldValue, Object newValue);
}
```

### 2.2 内置策略

**ReplaceStrategy** - 替换策略

```java
public class ReplaceStrategy implements KeyStrategy {
    @Override
    public Object apply(Object oldValue, Object newValue) {
        return newValue;
    }
}
```

**AppendStrategy** - 追加策略

```java
public class AppendStrategy implements KeyStrategy {
    @Override
    public Object apply(Object oldValue, Object newValue) {
        List<Object> result = new ArrayList<>();
        // 将旧值和新值都添加到列表
        if (oldValue instanceof List) {
            result.addAll((List<?>) oldValue);
        } else if (oldValue != null) {
            result.add(oldValue);
        }
        if (newValue instanceof List) {
            result.addAll((List<?>) newValue);
        } else if (newValue != null) {
            result.add(newValue);
        }
        return result;
    }
}
```

**LastValueStrategy** - 保留最后值策略

```java
public class LastValueStrategy implements KeyStrategy {
    @Override
    public Object apply(Object oldValue, Object newValue) {
        return newValue != null ? newValue : oldValue;
    }
}
```

### 2.3 KeyStrategyFactory

状态策略工厂。

**包路径**: `com.alibaba.cloud.ai.graph.KeyStrategyFactory`

```java
public class KeyStrategyFactory {
    public static KeyStrategyFactoryBuilder builder();
    Map<String, KeyStrategy> getStrategies();
}
```

**示例**：

```java
KeyStrategyFactory factory = KeyStrategyFactoryBuilder.builder()
    .withKey("messages", new AppendStrategy())
    .withKey("result", new ReplaceStrategy())
    .build();
```

---

## 3. 动作接口

### 3.1 AsyncNodeAction

异步节点动作接口。

**包路径**: `com.alibaba.cloud.ai.graph.action.AsyncNodeAction`

```java
@FunctionalInterface
public interface AsyncNodeAction {
    CompletableFuture<Map<String, Object>> apply(OverAllState state);
}
```

### 3.2 AsyncNodeActionWithConfig

带配置的异步节点动作。

**包路径**: `com.alibaba.cloud.ai.graph.action.AsyncNodeActionWithConfig`

```java
@FunctionalInterface
public interface AsyncNodeActionWithConfig {
    CompletableFuture<Map<String, Object>> apply(OverAllState state, RunnableConfig config);
}
```

### 3.3 AsyncCommandAction

异步命令动作，用于条件路由。

**包路径**: `com.alibaba.cloud.ai.graph.action.AsyncCommandAction`

```java
@FunctionalInterface
public interface AsyncCommandAction {
    CompletableFuture<Command> apply(OverAllState state, RunnableConfig config);
}
```

### 3.4 AsyncMultiCommandAction

多命令动作，用于并行路由。

**包路径**: `com.alibaba.cloud.ai.graph.action.AsyncMultiCommandAction`

```java
@FunctionalInterface
public interface AsyncMultiCommandAction {
    CompletableFuture<List<Command>> apply(OverAllState state, RunnableConfig config);
}
```

### 3.5 Command

节点跳转和状态更新指令。

**包路径**: `com.alibaba.cloud.ai.graph.action.Command`

```java
public class Command {
    private final String gotoNode;
    private final Map<String, Object> update;

    // 构造方法
    public Command(String gotoNode);
    public Command(String gotoNode, Map<String, Object> update);
    public Command(Map<String, Object> update);

    // 工厂方法
    public static Command end();
    public static Command update(Map<String, Object> update);

    // 访问方法
    public String gotoNode();
    public Map<String, Object> update();
}
```

**示例**：

```java
// 简单路由
Command next = new Command("nextNode");

// 带状态更新的路由
Command next = new Command("nextNode", Map.of("key", "value"));

// 仅更新状态
Command update = new Command(Map.of("key", "value"));
```

---

## 4. 配置类

### 4.1 CompileConfig

编译配置。

**包路径**: `com.alibaba.cloud.ai.CompileConfig`

```java
public class CompileConfig {
    // Builder
    public static Builder builder();

    // 配置访问
    public Optional<BaseCheckpointSaver> checkpointSaver();
    public List<GraphLifecycleListener> lifecycleListeners();
    public Set<String> interruptsBefore();
    public Set<String> interruptsAfter();
    public boolean interruptBeforeEdge();
    public int maxIterations();

    public static class Builder {
        public Builder saverConfig(SaverConfig saverConfig);
        public Builder lifecycleListeners(List<GraphLifecycleListener> listeners);
        public Builder interruptsBefore(Set<String> nodes);
        public Builder interruptsAfter(Set<String> nodes);
        public Builder interruptBeforeEdge(boolean flag);
        public Builder maxIterations(int max);
        public CompileConfig build();
    }
}
```

**示例**：

```java
CompileConfig config = CompileConfig.builder()
    .saverConfig(SaverConfig.builder()
        .register(new MemorySaver())
        .build())
    .interruptsBefore(Set.of("humanReview"))
    .lifecycleListeners(List.of(new LoggingListener()))
    .build();
```

### 4.2 RunnableConfig

运行时配置。

**包路径**: `com.alibaba.cloud.ai.graph.RunnableConfig`

```java
public class RunnableConfig {
    // 常量
    public static final String HUMAN_FEEDBACK_METADATA_KEY = "__human_feedback__";
    public static final String DEFAULT_PARALLEL_EXECUTOR_KEY = "__default_executor__";
    public static final String DEFAULT_PARALLEL_AGGREGATION_STRATEGY_KEY = "__default_aggregation_strategy__";

    // Builder
    public static Builder builder();
    public static Builder builder(RunnableConfig config);

    // 配置访问
    public Optional<String> threadId();
    public Optional<String> checkPointId();
    public <T> Optional<T> metadata(String key);
    public Map<String, Object> metadata();

    // 配置修改
    public RunnableConfig withCheckPointId(String checkPointId);
    public RunnableConfig withNodeResumed(String nodeId);

    public static class Builder {
        public Builder threadId(String threadId);
        public Builder checkPointId(String checkPointId);
        public Builder addMetadata(String key, Object value);
        public Builder metadata(Map<String, Object> metadata);
        public RunnableConfig build();
    }
}
```

**示例**：

```java
RunnableConfig config = RunnableConfig.builder()
    .threadId("conversation-001")
    .checkPointId("checkpoint-001")
    .addMetadata("__MAX_CONCURRENCY___node", 5)
    .build();
```

### 4.3 SaverConfig

持久化配置。

**包路径**: `com.alibaba.cloud.ai.graph.SaverConfig`

```java
public class SaverConfig {
    public static Builder builder();

    public Optional<BaseCheckpointSaver> checkpointSaver();

    public static class Builder {
        public Builder register(BaseCheckpointSaver saver);
        public SaverConfig build();
    }
}
```

---

## 5. 持久化接口

### 5.1 BaseCheckpointSaver

检查点保存器接口。

**包路径**: `com.alibaba.cloud.ai.graph.checkpoint.BaseCheckpointSaver`

```java
public interface BaseCheckpointSaver {
    String THREAD_ID_DEFAULT = "$default";

    // 获取最后一个检查点
    default Optional<Checkpoint> getLast(LinkedList<Checkpoint> checkpoints, RunnableConfig config);

    // 列出所有检查点
    Collection<Checkpoint> list(RunnableConfig config);

    // 获取指定检查点
    Optional<Checkpoint> get(RunnableConfig config);

    // 保存检查点
    RunnableConfig put(RunnableConfig config, Checkpoint checkpoint) throws Exception;

    // 释放检查点（清理线程）
    Tag release(RunnableConfig config) throws Exception;

    // 释放标签
    record Tag(String threadId, Collection<Checkpoint> checkpoints) {}
}
```

### 5.2 Checkpoint

检查点数据模型。

**包路径**: `com.alibaba.cloud.ai.graph.checkpoint.Checkpoint`

```java
public class Checkpoint {
    // Builder
    public static Builder builder();

    // 访问方法
    public String getId();
    public String getParentCheckpointId();
    public Map<String, Object> getState();
    public String getNodeId();
    public String getNextNodeId();
    public LocalDateTime getCreatedAt();

    // 状态更新
    public Checkpoint updateState(Map<String, Object> values, Map<String, KeyStrategy> channels);

    public static class Builder {
        public Builder id(String id);
        public Builder parentCheckpointId(String parentCheckpointId);
        public Builder state(Map<String, Object> state);
        public Builder nodeId(String nodeId);
        public Builder nextNodeId(String nextNodeId);
        public Checkpoint build();
    }
}
```

### 5.3 内置持久化实现

| 实现类 | 包路径 | 说明 |
|--------|--------|------|
| `MemorySaver` | `com.alibaba.cloud.ai.graph.checkpoint.savers.MemorySaver` | 内存存储 |
| `PostgresSaver` | `com.alibaba.cloud.ai.graph.checkpoint.savers.postgresql.PostgresSaver` | PostgreSQL |
| `MysqlSaver` | `com.alibaba.cloud.ai.graph.checkpoint.savers.mysql.MysqlSaver` | MySQL |
| `OracleSaver` | `com.alibaba.cloud.ai.graph.checkpoint.savers.oracle.OracleSaver` | Oracle |
| `MongoSaver` | `com.alibaba.cloud.ai.graph.checkpoint.savers.mongo.MongoSaver` | MongoDB |
| `RedisSaver` | `com.alibaba.cloud.ai.graph.checkpoint.savers.redis.RedisSaver` | Redis |
| `FileSystemSaver` | `com.alibaba.cloud.ai.graph.checkpoint.savers.file.FileSystemSaver` | 文件系统 |

---

## 6. 流式输出

### 6.1 NodeOutput

节点输出接口。

**包路径**: `com.alibaba.cloud.ai.graph.NodeOutput`

```java
public interface NodeOutput {
    String node();
    Map<String, Object> state();
}
```

### 6.2 StreamingOutput

流式输出实现。

**包路径**: `com.alibaba.cloud.ai.graph.streaming.StreamingOutput`

```java
public class StreamingOutput<T> implements NodeOutput {
    // 构造方法
    public StreamingOutput(T chunk, String nodeId, String agentName,
            OverAllState state, OutputType outputType);

    // 访问方法
    public T chunk();
    public String nodeId();
    public String agentName();
    public OutputType outputType();
    public boolean isSubGraph();
    public void setSubGraph(boolean subGraph);

    // 输出类型枚举
    public enum OutputType {
        CHUNK,    // 流式数据块
        COMPLETE, // 完整输出
        ERROR     // 错误输出
    }
}
```

### 6.3 GraphFlux

图流包装器。

**包路径**: `com.alibaba.cloud.ai.graph.streaming.GraphFlux`

```java
public record GraphFlux<T>(
    String nodeId,
    String key,
    Flux<T> flux,
    Function<T, Map<String, Object>> mapResult,
    Function<T, T> chunkResult
) {
    public static <T> GraphFlux<T> of(String nodeId, String key, Flux<T> flux,
            Function<T, Map<String, Object>> mapResult,
            Function<T, T> chunkResult);
}
```

### 6.4 ParallelGraphFlux

并行图流包装器。

**包路径**: `com.alibaba.cloud.ai.graph.streaming.ParallelGraphFlux`

```java
public class ParallelGraphFlux {
    public static ParallelGraphFlux of(List<GraphFlux<?>> graphFluxes);
    public boolean isEmpty();
    public List<GraphFlux<?>> getGraphFluxes();
}
```

---

## 7. 生命周期接口

### 7.1 GraphLifecycleListener

图生命周期监听器接口。

**包路径**: `com.alibaba.cloud.ai.graph.GraphLifecycleListener`

```java
public interface GraphLifecycleListener {
    String EXECUTION_ID_KEY = "executionId";

    // 图开始
    void onStart(String nodeId, Map<String, Object> state, RunnableConfig config);

    // 图结束
    void onComplete(String nodeId, Map<String, Object> state, RunnableConfig config);

    // 节点执行前
    void before(String nodeId, Map<String, Object> state, RunnableConfig config, long startTime);

    // 节点执行后
    void after(String nodeId, Map<String, Object> state, RunnableConfig config, long endTime);

    // 发生错误
    void onError(String nodeId, Map<String, Object> state, Exception e, RunnableConfig config);
}
```

**示例**：

```java
public class LoggingListener implements GraphLifecycleListener {
    @Override
    public void onStart(String nodeId, Map<String, Object> state, RunnableConfig config) {
        System.out.println("Graph started at node: " + nodeId);
    }

    @Override
    public void before(String nodeId, Map<String, Object> state, RunnableConfig config, long startTime) {
        System.out.println("Starting node: " + nodeId);
    }

    @Override
    public void after(String nodeId, Map<String, Object> state, RunnableConfig config, long endTime) {
        System.out.println("Completed node: " + nodeId);
    }

    @Override
    public void onError(String nodeId, Map<String, Object> state, Exception e, RunnableConfig config) {
        System.err.println("Error at node " + nodeId + ": " + e.getMessage());
    }

    @Override
    public void onComplete(String nodeId, Map<String, Object> state, RunnableConfig config) {
        System.out.println("Graph completed at node: " + nodeId);
    }
}
```

---

## 8. 并行执行

### 8.1 NodeAggregationStrategy

节点聚合策略枚举。

**包路径**: `com.alibaba.cloud.ai.graph.NodeAggregationStrategy`

```java
public enum NodeAggregationStrategy {
    ALL_OF,  // 等待所有分支完成
    ANY_OF   // 等待第一个完成的分支
}
```

### 8.2 ParallelNode

并行节点。

**包路径**: `com.alibaba.cloud.ai.graph.internal.node.ParallelNode`

```java
public class ParallelNode extends Node {
    public static final String PARALLEL_PREFIX = "__PARALLEL__";
    public static final String MAX_CONCURRENCY_KEY = "__MAX_CONCURRENCY__";

    // 格式化节点 ID
    public static String formatNodeId(String nodeId);

    // 获取执行器
    public static Executor getExecutor(RunnableConfig config, String nodeId);

    // 获取聚合策略
    public static NodeAggregationStrategy getAggregationStrategy(RunnableConfig config, String targetNodeId);

    // 是否为并行节点
    @Override
    public boolean isParallel();
}
```

---

## 9. 异常类

### 9.1 GraphStateException

图状态异常。

**包路径**: `com.alibaba.cloud.ai.graph.exception.GraphStateException`

```java
public class GraphStateException extends Exception {
    public Errors error();
    public String message();
}
```

### 9.2 Errors

错误类型枚举。

**包路径**: `com.alibaba.cloud.ai.graph.exception.Errors`

```java
public enum Errors {
    invalidNodeIdentifier,      // 无效节点标识
    missingNodeReferencedByEdge, // 边引用缺失节点
    missingEdge,                // 缺失边
    invalidEdgeTarget,          // 无效边目标
    duplicateEdgeTargetError,   // 重复的边目标
    missingNodeInEdgeMapping,   // 边映射中缺失节点
    executionError,             // 执行错误
    // ...
}
```

---

## 10. 工具类

### 10.1 StateSnapshot

状态快照。

**包路径**: `com.alibaba.cloud.ai.graph.state.StateSnapshot`

```java
public class StateSnapshot implements NodeOutput {
    public static StateSnapshot of(
        Map<String, KeyStrategy> keyStrategyMap,
        Checkpoint checkpoint,
        RunnableConfig config,
        StateFactory stateFactory);

    public Checkpoint checkpoint();
    public RunnableConfig config();
}
```

### 10.2 StateSerializer

状态序列化器。

**包路径**: `com.alibaba.cloud.ai.graph.serializer.StateSerializer`

```java
public interface StateSerializer {
    String serialize(Map<String, Object> state) throws Exception;
    Map<String, Object> deserialize(String data) throws Exception;
    <T> T cloneObject(T object) throws Exception;
}
```

### 10.3 OverAllStateBuilder

状态构建器。

**包路径**: `com.alibaba.cloud.ai.graph.OverAllStateBuilder`

```java
public class OverAllStateBuilder {
    public static Builder builder();

    public static class Builder {
        public Builder withKeyStrategies(Map<String, KeyStrategy> keyStrategies);
        public Builder withData(Map<String, Object> data);
        public Builder withStore(Store store);
        public OverAllState build();
    }
}
```

---

## 11. 输入输出类型

### 11.1 GraphResponse

图响应包装器。

**包路径**: `com.alibaba.cloud.ai.graph.GraphResponse`

```java
public class GraphResponse<T> {
    // 工厂方法
    public static <T> GraphResponse<T> of(T value);
    public static <T> GraphResponse<T> done(Object result);
    public static <T> GraphResponse<T> error(Throwable error);

    // 访问方法
    public CompletableFuture<T> getOutput();
    public Optional<Object> resultValue();
    public boolean isError();
}
```

### 11.2 IntendedNode

预期节点标记。

**包路径**: `com.alibaba.cloud.ai.graph.IntendedNode`

```java
public class IntendedNode {
    public static final String DEFAULT_ID = "__DEFAULT__";

    public static IntendedNode of(String nodeId, Map<String, Object> state);
}
```

---

## 12. 完整示例

### 12.1 完整工作流示例

```java
public class CompleteExample {
    public static void main(String[] args) throws Exception {
        // 1. 创建状态策略工厂
        KeyStrategyFactory factory = KeyStrategyFactoryBuilder.builder()
            .withKey("messages", new AppendStrategy())
            .withKey("result", new ReplaceStrategy())
            .build();

        // 2. 创建图
        StateGraph graph = new StateGraph(factory);

        // 3. 添加节点
        graph.addNode("input", (state, config) -> {
            String input = state.value("input", "");
            return CompletableFuture.completedFuture(Map.of(
                "messages", List.of(new UserMessage(input))
            ));
        });

        graph.addNode("process", (state, config) -> {
            List<Message> messages = state.value("messages", new ArrayList<>());
            // 处理逻辑...
            return CompletableFuture.completedFuture(Map.of(
                "result", "Processed: " + messages.size() + " messages"
            ));
        });

        graph.addNode("output", (state, config) -> {
            String result = state.value("result", "");
            System.out.println("Final result: " + result);
            return CompletableFuture.completedFuture(Map.of());
        });

        // 4. 添加边
        graph.addEdge(StateGraph.START, "input")
            .addEdge("input", "process")
            .addConditionalEdges("process",
                (state, config) -> {
                    String result = state.value("result", "");
                    if (result.contains("error")) {
                        return CompletableFuture.completedFuture(new Command("error"));
                    }
                    return CompletableFuture.completedFuture(new Command("success"));
                },
                Map.of("success", "output", "error", "error_handler")
            )
            .addEdge("output", StateGraph.END);

        graph.addNode("error_handler", (state, config) ->
            CompletableFuture.completedFuture(Map.of("result", "Error handled"))
        );
        graph.addEdge("error_handler", StateGraph.END);

        // 5. 配置
        CompileConfig config = CompileConfig.builder()
            .saverConfig(SaverConfig.builder()
                .register(MemorySaver.builder().build())
                .build())
            .lifecycleListeners(List.of(new LoggingListener()))
            .build();

        // 6. 编译
        CompiledGraph compiled = graph.compile(config);

        // 7. 执行
        RunnableConfig runConfig = RunnableConfig.builder()
            .threadId("example-001")
            .build();

        Map<String, Object> inputs = Map.of("input", "Hello World");
        Optional<OverAllState> result = compiled.invoke(inputs, runConfig);

        result.ifPresent(state ->
            System.out.println("Final state: " + state.data())
        );
    }
}
```

### 12.2 流式执行示例

```java
public class StreamingExample {
    public static void main(String[] args) {
        StateGraph graph = createGraph();
        CompiledGraph compiled = graph.compile();

        Map<String, Object> inputs = Map.of("input", "Hello");

        // 流式执行
        compiled.stream(inputs)
            .doOnNext(output -> {
                if (output instanceof StreamingOutput<?> streaming) {
                    System.out.println("Stream chunk: " + streaming.chunk());
                } else {
                    System.out.println("Node output: " + output.node());
                }
            })
            .doOnComplete(() -> System.out.println("Stream completed"))
            .blockLast();
    }
}
```
