# LLM 应用记忆架构设计

## 概述

在 SAA Graph 应用中，"记忆"不是单一概念，而是多层设计。本文档描述三层记忆体系的职责划分，以及 MemorySaver（图状态快照）与业务记忆的边界。

## 三层记忆体系

```
┌──────────────────────────────────────────────┐
│  Layer 1: 用户角色记忆（个性化）               │
│  存储：ConcurrentHashMap（内存）               │
│  key：userId:sessionId                        │
│  更新：LLM 提取 + 置信度融合                  │
├──────────────────────────────────────────────┤
│  Layer 2: 对话历史（多轮上下文）               │
│  存储：MessageWindowChatMemory（滑动窗口）     │
│  key：sessionId                               │
│  更新：每轮问答自动写入                        │
├──────────────────────────────────────────────┤
│  Layer 3: 研究报告（任务结果存档）             │
│  存储：内存 Map 或 Redis（TTL=24h）            │
│  key：threadId                                │
│  更新：ReporterNode 完成时写入                 │
└──────────────────────────────────────────────┘
```

## session_id vs thread_id 的记忆归属

| 维度 | session_id | thread_id |
|------|-----------|-----------|
| 含义 | 用户会话，跨多次任务不变 | 单次图执行，每次请求生成 |
| 格式 | 客户端传入，默认 `"__default__"` | `"{sessionId}-{count}"` 自动生成 |
| 管理的记忆 | 对话历史、角色记忆 | 报告存档、图状态快照 |
| 关系 | 一个 session 包含多个 thread | 每个 thread 属于一个 session |

```
session_id: "user-abc"
  ├── thread_id: "user-abc-1" → 报告A
  ├── thread_id: "user-abc-2" → 报告B
  └── thread_id: "user-abc-3" → 报告C（当前）
           ↑
    MessageWindowChatMemory 以 sessionId 为 key
    积累所有 thread 的对话历史（跨任务连续）
```

## MemorySaver 的职责边界

`MemorySaver` 是图框架的**执行状态快照**，与业务记忆完全独立：

| | MemorySaver（图状态快照） | 业务记忆（Layer 1-3） |
|---|---|---|
| 存储内容 | 整个 OverAllState 序列化快照 | 用户角色、对话历史、报告 |
| key | threadId（via RunnableConfig） | sessionId / threadId |
| 用途 | Human-in-the-loop 断点恢复 | 多轮对话上下文、个性化 |
| 生命周期 | 与单次图执行绑定 | 跨多次执行持续积累 |

```java
// MemorySaver 配置（仅用于 human_feedback 断点恢复）
compiledGraph = stateGraph.compile(CompileConfig.builder()
    .saverConfig(SaverConfig.builder()
        .register("memory", new MemorySaver())
        .build())
    .interruptBefore("human_feedback")  // 在此节点前挂起
    .build());

// 恢复执行（注入反馈后继续）
StateSnapshot snapshot = compiledGraph.getState(runnableConfig);
OverAllState state = snapshot.state();
state.withResume();
state.withHumanFeedback(new HumanFeedback(feedbackMap, "resume_node"));
compiledGraph.fluxStreamFromInitialNode(state, runnableConfig);
```

## 关键 Tradeoff

### 1. 存储后端：内存 vs 持久化

默认内存实现简单，但服务重启所有记忆丢失。**最严重的问题是 MemorySaver 也是内存实现**——服务重启会丢失所有 `interruptBefore` 挂起的状态，Human-in-the-loop 不可用于生产。

生产化优先级：
1. **MemorySaver → PostgresSaver/RedisSaver**（Human-in-the-loop 可靠性）
2. Layer 3 报告 → Redis（框架已支持切换，配置 `redis.enabled=true`）
3. Layer 1/2 → 根据 SLA 决定

### 2. LLM 调用代价 vs 个性化质量

Layer 1 角色记忆在**每轮对话开始时**触发 1~2 次 LLM 调用（提取 + 可能的融合）。这增加了首字延迟。如果场景对个性化要求不高，可以：
- `GuideScope.NONE`：完全跳过角色记忆节点
- 降低触发频率（如每 N 次调用才更新一次）

### 3. 对话历史窗口大小

`MessageWindowChatMemory` 默认 100 条。深度研究场景中每条 AssistantMessage 可能是完整报告，全量注入 LLM 上下文 token 消耗极大。合理的方向是**分层压缩**：近期保留原文，历史摘要化。当前框架未内置此能力，需自行实现。

### 4. 记忆时效

当前实现中角色记忆和对话历史**永不过期**，用户的角色特征随时间变化会导致记忆失效。建议通过 `interactionCount` 或时间戳实现**置信度衰减**，而非硬删除（避免老用户体验退化）。

### 5. 多用户扩展

实现中 `userId` 常被 Mock 为固定值，记忆 key 形如 `"MOCK_USER_ID:sessionId"`。支持真实多用户需要在所有记忆路径上注入真实 userId，涉及节点、Repository、Controller 全链路改动，是一个显著的扩展成本点。

## Spring AI MessageWindowChatMemory 使用

```java
// 配置（需要 short-term-memory.enabled=true）
MessageWindowChatMemory memory = MessageWindowChatMemory.builder()
    .chatMemoryRepository(new InMemoryChatMemoryRepository())
    .maxMessages(100)  // 滑动窗口大小
    .build();

// 写入（节点内）
memory.add(sessionId, new UserMessage(query));
memory.add(sessionId, new AssistantMessage(finalReport));

// 读取（注入 LLM 上下文）
List<Message> history = memory.get(sessionId);
messages.addAll(history);  // 拼入 prompt
```

## 相关文档

- [development-guide.md](./development-guide.md) - 状态恢复与中断（MemorySaver 用法）
- [dispatcher-routing-pattern.md](./dispatcher-routing-pattern.md) - 节点路由设计
