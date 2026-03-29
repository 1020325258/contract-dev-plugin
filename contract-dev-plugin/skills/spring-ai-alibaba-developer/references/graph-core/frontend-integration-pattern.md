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

## 注意事项

- **nodeName 是核心标识**：前后端通过 nodeName 协调内容的展示逻辑
- **visible 字段控制渲染**：LLM 流式输出通过 visible 标志控制是否展示给用户
- **类型 B 消息的 content 结构取决于 nodeName**：不同节点的 content 格式不同
- **前端需解析 JSON 数组**：后端返回的是 JSON 数组，前端按 nodeName 过滤

## 相关链接

- [streaming-output-pattern.md](./streaming-output-pattern.md) - SSE 流式输出集成模式
- [multi-agent-coordination-pattern.md](./multi-agent-coordination-pattern.md) - 多 Agent 协作编排
