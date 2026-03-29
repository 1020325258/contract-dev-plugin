# Graph + SSE 流式输出集成模式

## 概述

将 SAA Graph 执行结果通过 Spring WebFlux SSE 推送给前端的完整设计模式，包含双消息类型设计和 FluxConverter 的使用。

## 整体架构

```
compiledGraph.fluxStream()         // 返回 Flux<NodeOutput>
  → GraphProcess.processStream()   // 分类处理，推送 SSE
  → Sinks.Many<ServerSentEvent>    // Reactor 单播 Sink
  → 前端 SSE 连接
```

## Controller 层：返回 SSE Flux

```java
@PostMapping(value = "/stream", produces = MediaType.TEXT_EVENT_STREAM_VALUE)
public Flux<ServerSentEvent<String>> chatStream(@RequestBody ChatRequest request) {
    Map<String, Object> inputs = buildInputs(request);
    RunnableConfig config = RunnableConfig.builder()
        .threadId(request.getThreadId())
        .build();

    // Sink：多播/单播推送
    Sinks.Many<ServerSentEvent<String>> sink =
        Sinks.many().unicast().onBackpressureBuffer();

    // 启动图执行，结果异步推入 sink
    CompletableFuture<Void> future = graphProcess.processStream(
        graphId, compiledGraph.fluxStream(inputs, config), sink);

    graphProcess.registerFuture(graphId, future);  // 支持 stop

    return sink.asFlux();
}
```

## 双消息类型设计

Graph 执行过程中产生两类输出，需区分处理：

### 类型 A：LLM Token 流（StreamingOutput）

节点正在生成内容时，每个 token 推送一帧：

```json
{
  "reporter_llm_stream": "AI 生成的文本片段...",
  "step_title": "报告生成",
  "visible": true,
  "finishReason": "stop",
  "graphId": { "session_id": "xxx", "thread_id": "xxx-1" }
}
```

**`visible` 字段**：控制前端是否渲染该节点的流式输出。例如 planner 节点的内部思考过程设置 `visible=false`，不展示给用户，但其结果仍完整写入 State 供后续节点使用。

```java
public enum StreamNodePrefixEnum {
    PLANNER_LLM_STREAM("planner_llm_stream", false),      // 隐藏
    RESEARCHER_LLM_STREAM("researcher_llm_stream", true),  // 显示
    REPORTER_LLM_STREAM("reporter_llm_stream", true);      // 显示

    private final String prefix;
    private final boolean visible;
}
```

### 类型 B：节点完成事件（NodeOutput）

节点执行结束后推送一次：

```json
{
  "nodeName": "reporter",
  "displayTitle": "报告生成",
  "content": "# 最终报告\n...",
  "graphId": { "session_id": "xxx", "thread_id": "xxx-1" },
  "siteInformation": [{ "title": "...", "url": "..." }]
}
```

`displayTitle` 为空的节点（如内部路由节点）不推送此消息。

### 消息分发逻辑

```java
// GraphProcess.processStream() 核心逻辑
graphFlux.doOnNext(nodeOutput -> {
    String content;
    if (nodeOutput instanceof StreamingOutput streaming) {
        // 类型 A：带 visible 标志的 token 流
        content = buildLLMNodeContent(nodeName, graphId, streaming);
    } else {
        // 类型 B：节点完成事件，按 nodeName switch 提取特定字段
        content = buildNormalNodeContent(graphId, nodeName, nodeOutput);
    }
    if (StringUtils.isNotEmpty(content)) {
        sink.tryEmitNext(ServerSentEvent.builder(content).build());
    }
}).subscribe();
```

## FluxConverter：节点内包装 LLM 流式输出

节点 `apply()` 无法直接返回流式数据（返回类型是 `Map`），需要通过 `FluxConverter` 将 `Flux<ChatResponse>` 转换为写入 State 的同步结果，同时让框架感知到有流式数据需要推送：

```java
// 节点内部：将 LLM 流式响应包装进图框架
return FluxConverter.buildWithChatResponse(
    chatModel.stream(prompt),                    // Flux<ChatResponse>
    chunk -> new StreamingOutput(prefix, chunk), // 每帧 → StreamingOutput
    response -> Map.of(                          // 完成时写入 State
        "final_report", response.getResult().getOutput().getText()
    )
);
```

`FluxConverter` 的工作机制：
- 逐帧将 `ChatResponse` 包装为 `StreamingOutput` 推入框架的流管道
- 最后一帧完成时，调用 `mapResult` 函数生成写入 `OverAllState` 的 Map
- 框架保证：State 在整个流完成后才更新，不影响流式推送过程

## 停止任务

```java
// 注册 Future，支持外部中断
ConcurrentHashMap<GraphId, Future<?>> futureMap;

// 停止时
futureMap.get(graphId).cancel(true);  // 触发 InterruptedException
// 向 sink 推送终止消息
sink.tryEmitNext(ServerSentEvent.builder(TASK_STOPPED_MESSAGE).build());
```

## 注意事项

- **`visible` 只影响前端渲染，不影响 State 写入**：隐藏节点的数据仍完整流转
- **类型 B 消息按 `nodeName` switch 提取特定字段**：不同节点的 `content` 内容不同（有的是 JSON、有的是 Markdown 字符串）
- **Sinks.Many 需选择合适的背压策略**：单个用户连接用 `unicast()`，多订阅者用 `multicast()`

## 相关文档

- [development-guide.md](./development-guide.md) - 流式执行基础示例（`compiled.stream()`）
- [dispatcher-routing-pattern.md](./dispatcher-routing-pattern.md) - 节点路由设计
