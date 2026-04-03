# 前端集成模式：nodeName 标识与消息分发

## 概述

本文档记录 DeepResearch 项目中前后端通过 SSE 进行交互的设计模式，包括 nodeName 标识机制、消息分发逻辑和前端解析流程。

## 背景

DeepResearch 是基于 Spring AI Alibaba Graph 的 AI 研究自动化平台，需要将后端多 Agent 的执行状态实时推送给前端 Vue3 应用。关键挑战包括：
- 后端有多个 Agent 节点（Coordinator、Planner、Researcher、Reporter 等）
- 前端需要根据不同节点展示不同内容
- 需要区分 LLM 流式输出和节点完成事件

## 核心内容

### nodeName 标识机制

后端通过 `nodeName` 字段标识当前执行的节点：

```java
// NodeNameEnum.java
public enum NodeNameEnum {
    START("__START__", "开始"),
    COORDINATOR("coordinator", "意图识别"),
    REWRITE_MULTI_QUERY("rewrite_multi_query", "查询问题相关信息"),
    BACKGROUND_INVESTIGATOR("background_investigator", "背景调查"),
    PLANNER("planner", "研究计划"),
    RESEARCH_TEAM("research_team", "等待并行节点执行完成"),
    REPORTER("reporter", "报告生成"),
    END("__END__", "结束");
}
```

### SSE 消息格式

两种消息类型共用同一 JSON 结构，通过内容区分：

```json
// 类型 A：LLM Token 流（StreamingOutput）
{
  "reporter_llm_stream": "生成的文本片段...",
  "step_title": "报告生成",
  "visible": true,
  "finishReason": "stop",
  "graphId": { "session_id": "xxx", "thread_id": "xxx-1" }
}

// 类型 B：节点完成事件（NodeOutput）
{
  "nodeName": "coordinator",
  "graphId": { "session_id": "xxx", "thread_id": "xxx-1" },
  "displayTitle": "意图识别",
  "content": { "COORDINATOR": "是否深度研究..." },
  "siteInformation": []
}
```

### 后端消息构建（GraphProcess.java）

```java
// 根据节点类型构建不同内容
String content;
if (output instanceof StreamingOutput streamingOutput) {
    // 类型 A：LLM 流式输出
    content = buildLLMNodeContent(nodeName, graphId, streamingOutput, output);
} else {
    // 类型 B：节点完成事件
    content = buildNormalNodeContent(graphId, nodeName, output);
}

// 发送 SSE
sink.tryEmitNext(ServerSentEvent.builder(content).build());
```

### buildNormalNodeContent 按 nodeName 提取内容

```java
private String buildNormalNodeContent(GraphId graphId, String nodeName, NodeOutput output) {
    NodeNameEnum nodeEnum = NodeNameEnum.fromNodeName(nodeName);
    Object content = switch (nodeEnum) {
        case START -> output.state().data().get("query");
        case COORDINATOR -> output.state().data().get("deep_research");
        case PLANNER -> output.state().data().get("planner_content");
        case REPORTER -> output.state().data().get("final_report");
        case RESEARCH_TEAM -> output.state().data().get("research_team_content");
        default -> "";
    };

    NodeResponse response = new NodeResponse(nodeName, graphId, displayTitle, content, siteInformation);
    return OBJECT_MAPPER.writeValueAsString(response);
}
```

### 前端消息解析

```typescript
// useMessageParser.ts
const parseSuccessMessage = (msg: string) => {
    const jsonArray = parseJsonTextStrict(msg)

    // 按 nodeName 过滤节点
    const coordinatorNode = jsonArray.filter(item => item.nodeName === 'coordinator')[0]
    const backgroundNode = jsonArray.filter(item => item.nodeName === 'background_investigator')[0]
    const endNode = jsonArray.filter(item => item.nodeName === '__END__')[0]

    // 根据是否有 endNode 判断任务是否完成
}
```

### 前端展示（ThoughtChain）

前端使用 Ant Design Vue 的 `ThoughtChain` 组件展示：

```typescript
// 根据消息类型构建不同思考链
const buildStartDSThoughtChain = (jsonArray) => {
    // 背景调查节点
    const backgroundNode = jsonArray.filter(item => item.nodeName === 'background_investigator')[0]
    // 提取 siteInformation 渲染网站列表

    return h(ThoughtChain, { items: [...] })
}
```

## 一次 DeepResearch 完整节点输出序列

用户发起研究时，后端按以下顺序向前端推送消息：

```
__START__ → coordinator → rewrite_multi_query → background_investigator
→ planner → human_feedback → [并行] researcher_* / coder_* → reporter → __END__
```

### 流式节点 vs 非流式节点

| 节点 | 流式? | 说明 |
|---|---|---|
| `__START__` | ❌ | 一次性输出用户 query |
| `coordinator` | ❌ | 一次性输出意图识别结果 |
| `rewrite_multi_query` | ❌ | 一次性输出优化查询列表 |
| `background_investigator` | ❌ | 一次性输出调研网站列表 |
| `planner` | ❌ | 一次性输出任务规划 JSON |
| `human_feedback` | ❌ | 暂停等待用户确认 |
| `*_llm_stream` (并行) | ✅ | LLM 逐字流式输出，边输出边推送 |
| `reporter` | ❌ | 非流式的 reporter 节点 |
| `__END__` | ❌ | 一次性输出完整报告 |

### 各节点完整输出内容

#### __START__ (普通节点)
```json
{
  "nodeName": "__START__",
  "graphId": {"session_id": "abc", "thread_id": "abc-1"},
  "displayTitle": "开始",
  "content": {"query": "研究一下AI大模型最新进展"},
  "site_information": {}
}
```
**前端样式**: 卡片显示用户输入的 query

#### coordinator (普通节点)
```json
{
  "nodeName": "coordinator",
  "graphId": {...},
  "displayTitle": "深度研究",
  "content": {"research_query": "研究一下AI大模型最新进展", "search_engine": "tavily", "deep_research": true},
  "site_information": {}
}
```
**前端样式**: 卡片显示"深度研究"标题，开启研究模式

#### rewrite_multi_query (普通节点)
```json
{
  "nodeName": "rewrite_multi_query",
  "graphId": {...},
  "displayTitle": "查询问题相关信息",
  "content": {"optimize_queries": ["AI大模型最新发展动态 2025", "大型语言模型最新进展"]},
  "site_information": {}
}
```
**前端样式**: Markdown 渲染优化后的查询列表

#### background_investigator (普通节点)
```json
{
  "nodeName": "background_investigator",
  "graphId": {...},
  "displayTitle": "背景调查",
  "content": {...},
  "site_information": [[{"title": "OpenAI GPT-5发布", "url": "https://..."}]]
}
```
**前端样式**: ReferenceSources 组件渲染网站列表 + ThoughtChain 思维链卡片

#### planner (普通节点)
```json
{
  "nodeName": "planner",
  "graphId": {...},
  "displayTitle": "研究计划",
  "content": "{\"title\":\"AI大模型最新进展研究计划\",\"steps\":[...]}"
}
```
**前端样式**: Markdown 渲染任务步骤列表（### 标题 + 描述 + 分隔线）

#### 流式节点 (LLM Token 流)
```json
{
  "reporter_llm_stream": "# AI大模型最新进展研究报告\n\n## 一、技术架构\nGPT-5采用了...",
  "step_title": "生成报告",
  "visible": true,
  "finishReason": "STOP",
  "graphId": {...}
}
```
**前端样式**: MD 组件实时累积渲染 Markdown（标题、代码块、列表等），finishReason=STOP 时标记完成

#### __END__ (普通节点)
```json
{
  "nodeName": "__END__",
  "graphId": {...},
  "displayTitle": "结束",
  "content": {"final_report": "# AI大模型最新进展研究报告\n\n...", "reason": "正常完成"},
  "site_information": {}
}
```
**前端样式**: 完整 Markdown 报告 + 可折叠"参考来源"和"思路"思维链

## 前端 6 种渲染样式

| 样式 | 组件 | 触发场景 |
|---|---|---|
| **普通对话** | Bubble (ant-design-x-vue) | 普通聊天模式，左右布局 AI/用户 |
| **研究进度** | ThoughtChain | 研究过程中显示步骤卡片，pending/success/error 状态 |
| **LLM 流式输出** | MD (Markdown) | `*_llm_stream` 节点，实时累积渲染 |
| **Markdown 内容** | MD (Markdown) | planner/reporter 的 content 字段 |
| **HTML 报告** | HtmlRenderer | 可切换代码/预览 tab + iframe 全屏 |
| **网站引用** | ReferenceSources | background_investigator 的 siteInformation |

### 流式节点的前端累积逻辑

```typescript
// report/index.vue - 流式节点累积渲染
const llmStreamCache = new Map<string, { item: ThoughtChainItem; content: string }>()

// 每个 chunk 追加到缓存
cached.content += node[key]
// 更新 MD 组件内容（实时渲染）
cached.item.content = h(MD, { content: cached.content })
// 结束标记
if (node.finishReason === 'STOP') {
    cached.item.status = 'success'
    cached.item.icon = h(CheckCircleOutlined)
}
```

## 消息存储与解析

### 按 threadId 聚合存储
```typescript
// MessageStore.ts
addReport(report: any) {
    const node = JSON.parse(report)
    const threadId = node.graphId.thread_id
    if (!this.report[threadId]) {
        this.report[threadId] = []
    }
    this.report[threadId].push(node)  // 追加，每次 SSE 一个 chunk
}
```

### 状态机解析
```typescript
// useMessageParser.ts
const parseSuccessMessage = (msg: string) => {
    const arr = parseJsonTextStrict(msg)

    // 无 coordinator.content → 普通聊天
    const coordinatorNode = findNode(arr, 'coordinator')
    if (coordinatorNode && !coordinatorNode.content) {
        return { type: 'chat', content: endNode?.content.output }
    }

    // 无 __END__ → 正在执行
    if (!findNode(arr, '__END__')) {
        return { type: 'startDS', data: arr }
    }

    // 有 __END__ → 完成
    return { type: 'endDS', data: arr }
}
```

## 注意事项

- **nodeName 是核心标识**：前后端通过 nodeName 协调内容的展示逻辑
- **visible 字段控制渲染**：LLM 流式输出通过 visible 标志控制是否展示给用户
- **流式节点每个 token 一帧**：每次 SSE 推送一个 JSON，前端累积后渲染
- **普通节点一次性推送**：节点执行完成时才推送 content，不会在执行过程中推送中间状态
- **前端 report 按 threadId 聚合**：所有 chunk 存入数组，等流结束后统一解析渲染思维链

## 相关链接

- [streaming-output-pattern.md](./streaming-output-pattern.md) - SSE 流式输出集成模式（FluxConverter、双消息类型）
- [multi-agent-coordination-pattern.md](./multi-agent-coordination-pattern.md) - 多 Agent 协作编排
