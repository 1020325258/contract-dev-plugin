# Dispatcher 路由模式

## 概述

在 SAA Graph 应用中，节点与边的路由解耦通过一种约定实现：**节点写入控制键，EdgeAction（Dispatcher）读取控制键决策路由**。这是一种应用层约定，框架本身不强制，但实践中非常有效。

## 核心模式：节点写、边读

### 约定

每个需要条件路由的节点，在 `apply()` 返回的 Map 中写入一个控制键：

```java
// 节点内部决定下一跳，写入控制键
public Map<String, Object> apply(OverAllState state) {
    // ... 业务逻辑 ...
    String nextNode = condition ? "node_a" : "node_b";
    return Map.of(
        "coordinator_next_node", nextNode,  // 控制键，供 Dispatcher 读取
        "result", someResult                // 数据键，供后续节点使用
    );
}
```

对应的 Dispatcher（实现 `EdgeAction` 或 `AsyncCommandAction`）只负责读取该键：

```java
public class CoordinatorDispatcher implements AsyncCommandAction {
    @Override
    public CompletableFuture<Command> apply(OverAllState state, RunnableConfig config) {
        String next = (String) state.value("coordinator_next_node").orElse("__END__");
        return CompletableFuture.completedFuture(new Command(next));
    }
}
```

在 `StateGraph` 中注册条件边：

```java
stateGraph.addConditionalEdges(
    "coordinator",
    new CoordinatorDispatcher(),
    Map.of(
        "rewrite_multi_query", "rewrite_multi_query",
        "__END__", "__END__"
    )
);
```

### 控制键命名规范

`<节点名>_next_node`，全小写下划线，例如：
- `coordinator_next_node`
- `information_next_node`
- `research_team_next_node`

布尔类型决策键直接用语义名（如 `use_professional_kb`），由 Dispatcher 读取布尔值映射路由。

## 并行扇出 + 汇聚模式

动态并行任务的标准结构：

```
[分配节点]                [并行执行]           [汇聚节点]
parallel_executor  →  researcher_0, coder_0  →  research_team
                   →  researcher_1, coder_1  ↗
                   →  researcher_2          ↗
```

### 动态注册并行节点

并行节点数量由配置决定，在 `StateGraph` 构建阶段动态批量注册：

```java
// 批量注册 researcher_0, researcher_1, ...
for (int i = 0; i < researcherCount; i++) {
    String nodeId = "researcher_" + i;
    stateGraph.addNode(nodeId, node_async(new ResearcherNode(i, ...)));
    stateGraph.addEdge("parallel_executor", nodeId);  // 扇出
    stateGraph.addEdge(nodeId, "research_team");       // 汇聚
}
```

### 汇聚节点的循环设计

汇聚节点（research_team）检查所有任务是否完成，未完成时循环回分配节点：

```java
// research_team 节点：检查所有 step 是否完成
boolean allDone = plan.getSteps().stream()
    .allMatch(step -> step.getExecutionStatus().startsWith("done"));

// Dispatcher 读取并决策
String next = allDone ? "next_phase" : "parallel_executor";
return Map.of("research_team_next_node", next);
```

## 注意事项

- **控制键与数据键分离**：控制键只用于路由，执行完后不再有业务含义，可随时被覆盖（ReplaceStrategy）
- **Dispatcher 保持纯函数**：Dispatcher 只读状态、返回路由决策，不产生副作用
- **并行节点扇出时，框架会等待所有并行分支完成**后才推进汇聚节点

## 相关文档

- [core-design.md](./core-design.md) - EdgeCondition 和 AsyncCommandAction 接口设计
- [development-guide.md](./development-guide.md) - 条件路由和并行执行代码示例
