# Graph Core 核心设计分析

## 1. Graph 抽象设计

### 1.1 状态图模型

Spring AI Alibaba Graph Core 采用了**有向状态图**作为核心抽象模型。图由节点(Node)和边(Edge)组成，支持复杂的工作流编排。

```
┌─────────┐      ┌─────────┐      ┌─────────┐
│  START  │─────>│  Node A │─────>│  Node B │
└─────────┘      └─────────┘      └─────────┘
                        │
                        │ (条件路由)
                        v
                 ┌─────────┐
                 │  Node C │
                 └─────────┘
                        │
                        v
                 ┌─────────┐
                 │   END   │
                 └─────────┘
```

### 1.2 StateGraph 类设计

`StateGraph` 是图的定义类，采用**流式 Builder 模式**设计：

```java
public class StateGraph {
    // 图标识常量
    public static final String END = "__END__";
    public static final String START = "__START__";
    public static final String ERROR = "__ERROR__";

    // 核心数据结构
    final Nodes nodes = new Nodes();          // 节点集合
    final Edges edges = new Edges();          // 边集合

    // 配置组件
    private final KeyStrategyFactory keyStrategyFactory;  // 状态键策略工厂
    private final StateSerializer stateSerializer;       // 状态序列化器

    // 核心方法
    public StateGraph addNode(String id, AsyncNodeAction action);
    public StateGraph addEdge(String sourceId, String targetId);
    public StateGraph addConditionalEdges(String sourceId, AsyncCommandAction condition, Map<String, String> mappings);
    public CompiledGraph compile(CompileConfig config);
}
```

**设计特点**：
1. **不可变常量**：`START`、`END`、`ERROR` 作为图的固定标识
2. **封装集合**：`Nodes` 和 `Edges` 作为内部容器类，提供类型安全的操作
3. **流式 API**：`addNode()`、`addEdge()` 等方法返回 `this`，支持链式调用

### 1.3 CompiledGraph 设计

`CompiledGraph` 是编译后的图，负责：
- 存储编译后的节点工厂和边映射
- 提供执行入口 (`invoke()`, `stream()`)
- 管理状态持久化

```java
public class CompiledGraph {
    public final StateGraph stateGraph;
    public final CompileConfig compileConfig;

    // 节点工厂映射（线程安全设计）
    final Map<String, Node.ActionFactory> nodeFactories = new LinkedHashMap<>();

    // 边映射
    final Map<String, EdgeValue> edges = new LinkedHashMap<>();

    // 执行入口
    public Optional<OverAllState> invoke(Map<String, Object> inputs, RunnableConfig config);
    public Flux<NodeOutput> stream(Map<String, Object> inputs, RunnableConfig config);
}
```

**线程安全设计**：
- 使用 `Node.ActionFactory` 工厂模式而非直接存储实例
- 每次执行时通过工厂创建新的 Action 实例

### 1.4 节点类型层次

```
Node (基类)
├── SubCompiledGraphNode    # 已编译子图节点
├── SubStateGraphNode       # 未编译子图节点
├── ParallelNode            # 并行节点
└── ConditionalParallelNode # 条件并行节点
```

**Node 核心设计**：

```java
public class Node {
    public static final String PRIVATE_PREFIX = "__";

    public interface ActionFactory {
        AsyncNodeActionWithConfig apply(CompileConfig config) throws GraphStateException;
    }

    private final String id;
    private final ActionFactory actionFactory;

    public void validate() throws GraphStateException {
        // 验证节点 ID 有效性
        // 禁止以 "__" 开头的私有前缀
        // 禁止空白 ID
    }
}
```

## 2. 状态管理设计

### 2.1 OverAllState 状态容器

`OverAllState` 是核心状态容器，采用**策略模式**管理状态更新：

```java
public final class OverAllState implements Serializable {
    // 状态数据
    private final Map<String, Object> data;

    // 键策略映射
    private final Map<String, KeyStrategy> keyStrategies;

    // 长期存储
    private Store store;

    // 默认输入键
    public static final String DEFAULT_INPUT_KEY = "input";

    // 标记删除常量
    public static final Object MARK_FOR_REMOVAL = new Object();
}
```

**核心功能**：

| 方法 | 说明 |
|------|------|
| `updateState(Map)` | 根据策略更新状态 |
| `registerKeyAndStrategy(String, KeyStrategy)` | 注册键策略 |
| `value(String)` | 获取状态值 |
| `snapShot()` | 创建状态快照 |

### 2.2 KeyStrategy 策略接口

```java
@FunctionalInterface
public interface KeyStrategy extends BinaryOperator<Object> {

    // 默认策略常量
    KeyStrategy REPLACE = (oldValue, newValue) -> newValue;

    // 合并两个值
    Object apply(Object oldValue, Object newValue);
}
```

**内置策略实现**：

| 策略 | 行为 |
|------|------|
| `ReplaceStrategy` | 新值替换旧值 |
| `AppendStrategy` | 将新值追加到列表 |
| `LastValueStrategy` | 保留最后一个非空值 |
| `RemoveStrategy` | 移除指定键 |

### 2.3 状态更新流程

```
输入状态 ──────> KeyStrategy.apply() ──────> 更新后状态
                    │
                    ├── ReplaceStrategy: newValue
                    ├── AppendStrategy: oldValue + newValue
                    └── CustomStrategy: 自定义逻辑
```

**状态更新示例**：

```java
// 定义状态策略
KeyStrategyFactory factory = KeyStrategyFactoryBuilder.builder()
    .withKey("messages", new AppendStrategy())
    .withKey("result", new ReplaceStrategy())
    .build();

// 创建图
StateGraph graph = new StateGraph(factory);

// 节点更新状态
AsyncNodeAction action = (state) -> {
    List<Message> messages = state.value("messages", new ArrayList<>());
    messages.add(new Message("Hello"));
    return CompletableFuture.completedFuture(Map.of("messages", messages));
};
```

## 3. 持久化架构设计

### 3.1 Checkpoint 检查点模型

```java
public class Checkpoint {
    private final String id;              // 检查点唯一标识
    private Map<String, Object> state;    // 状态数据
    private String nodeId;                // 当前节点 ID
    private String nextNodeId;            // 下一个节点 ID

    public Checkpoint updateState(Map<String, Object> values, Map<String, KeyStrategy> channels);
}
```

### 3.2 BaseCheckpointSaver 接口

```java
public interface BaseCheckpointSaver {
    String THREAD_ID_DEFAULT = "$default";

    // 查询接口
    Collection<Checkpoint> list(RunnableConfig config);
    Optional<Checkpoint> get(RunnableConfig config);

    // 持久化接口
    RunnableConfig put(RunnableConfig config, Checkpoint checkpoint) throws Exception;

    // 释放接口
    Tag release(RunnableConfig config) throws Exception;

    record Tag(String threadId, Collection<Checkpoint> checkpoints) {}
}
```

### 3.3 持久化实现层次

```
BaseCheckpointSaver (接口)
        │
        └── MemorySaver (内存实现 - 基类)
                │
                ├── PostgresSaver   (PostgreSQL)
                ├── MysqlSaver      (MySQL)
                ├── OracleSaver     (Oracle)
                ├── MongoSaver      (MongoDB)
                ├── RedisSaver      (Redis)
                └── FileSystemSaver (文件系统)
```

### 3.4 PostgresSaver 数据模型

```sql
-- 线程表
CREATE TABLE GraphThread (
    thread_id UUID PRIMARY KEY,
    thread_name VARCHAR(255),
    is_released BOOLEAN DEFAULT FALSE NOT NULL
);

-- 检查点表
CREATE TABLE GraphCheckpoint (
    checkpoint_id UUID PRIMARY KEY,
    parent_checkpoint_id UUID,
    thread_id UUID NOT NULL,
    node_id VARCHAR(255),
    next_node_id VARCHAR(255),
    state_data JSONB NOT NULL,
    state_content_type VARCHAR(100) NOT NULL,
    saved_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_thread FOREIGN KEY(thread_id) REFERENCES GraphThread(thread_id) ON DELETE CASCADE
);
```

### 3.5 持久化配置示例

```java
// PostgreSQL 配置
PostgresSaver saver = PostgresSaver.builder()
    .host("localhost")
    .port(5432)
    .database("graph_db")
    .user("postgres")
    .password("password")
    .createTables(true)
    .stateSerializer(StateGraph.DEFAULT_JACKSON_SERIALIZER)
    .build();

// 编译配置
SaverConfig saverConfig = SaverConfig.builder()
    .register(saver)
    .build();

CompileConfig config = CompileConfig.builder()
    .saverConfig(saverConfig)
    .build();

// 编译图
CompiledGraph compiled = graph.compile(config);
```

## 4. 边与条件路由设计

### 4.1 Edge 结构

```java
public record Edge(String sourceId, List<EdgeValue> targets) {

    // 判断是否为并行边
    public boolean isParallel() {
        return targets.size() > 1;
    }

    // 获取单个目标（非并行边）
    public EdgeValue target() {
        if (isParallel()) {
            throw new IllegalStateException("Edge is parallel");
        }
        return targets.get(0);
    }
}
```

### 4.2 EdgeValue 设计

```java
public record EdgeValue(String id, EdgeCondition value) {

    // 静态目标边
    public EdgeValue(String targetId) {
        this(targetId, null);
    }

    // 条件路由边
    public EdgeValue withTargetIdsUpdated(Function<String, EdgeValue> newTarget);
}
```

### 4.3 EdgeCondition 条件设计

```java
public class EdgeCondition {
    private final AsyncCommandAction singleAction;    // 单命令动作
    private final AsyncMultiCommandAction multiAction; // 多命令动作
    private final Map<String, String> mappings;       // 路由映射

    public boolean isMultiCommand() {
        return multiAction != null;
    }

    public static EdgeCondition single(AsyncCommandAction action, Map<String, String> mappings);
    public static EdgeCondition multi(AsyncMultiCommandAction action, Map<String, String> mappings);
}
```

### 4.4 条件路由示例

```java
// 单条件路由
graph.addConditionalEdges("router",
    (state, config) -> {
        String type = state.value("type", "");
        return CompletableFuture.completedFuture(type);
    },
    Map.of(
        "A", "nodeA",
        "B", "nodeB",
        "default", "nodeDefault"
    )
);

// 多条件并行路由
graph.addParallelConditionalEdges("parallelRouter",
    (state, config) -> {
        return CompletableFuture.completedFuture(List.of("A", "B"));
    },
    Map.of(
        "A", "nodeA",
        "B", "nodeB"
    )
);
```

## 5. 设计模式应用

### 5.1 Builder 模式
- `StateGraph` 的流式 API
- `CompileConfig`、`RunnableConfig` 配置构建
- 各 Saver 的 Builder

### 5.2 工厂模式
- `Node.ActionFactory` 节点动作工厂
- `KeyStrategyFactory` 策略工厂

### 5.3 策略模式
- `KeyStrategy` 状态合并策略
- 支持自定义扩展

### 5.4 模板方法模式
- `BaseGraphExecutor` 执行器基类
- `MemorySaver` 作为 Saver 基类

### 5.5 观察者模式
- `GraphLifecycleListener` 生命周期监听
- 支持多个监听器注册
