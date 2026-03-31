# Agent RAG Tool 模式

## 概述
将 RAG 能力封装为 Tool，由 Agent 智能决策何时调用检索。

## 架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                Agent + RAG 架构                                 │
├─────────────────────────────────────────────────────────────────┤
│  MCP Server / Skill                                              │
│       ↓                                                          │
│  ┌─────────────────────────┐                                    │
│  │ KnowledgeRetrievalTool  │  ← 实现为标准 Tool                  │
│  │ - vectorStore           │                                    │
│  │ - similaritySearch()    │                                    │
│  └─────────────────────────┘                                    │
│       ↓                                                          │
│  ToolCallback 注册到 Agent                                       │
│       ↓                                                          │
│  Agent 智能调用（需要时才检索）                                    │
└─────────────────────────────────────────────────────────────────┘
```

## 实现步骤

### Step 1：创建 RAG Tool

```java
// 从 rag-agent-example/KnowledgeRetrievalTool.java
@Component
public class KnowledgeRetrievalTool implements BiFunction<Request, ToolContext, String> {

    private final SimpleVectorStore vectorStore;

    @PostConstruct
    void initKnowledgeBase() {
        // 从 URL 加载文档
        for (String url : knowledgeSourceUrls) {
            JsoumDocumentReader reader = new JsoupDocumentReader(url);
            List<Document> documents = reader.get();
            TokenTextSplitter splitter = new TokenTextSplitter();
            vectorStore.add(splitter.apply(documents));
        }
    }

    @Override
    public String apply(Request request, ToolContext toolContext) {
        SearchRequest searchRequest = SearchRequest.builder()
            .query(request.query())
            .topK(request.topK() != null ? request.topK() : 4)
            .build();

        List<Document> documents = vectorStore.similaritySearch(searchRequest);

        if (documents.isEmpty()) {
            return "No relevant information found in the knowledge base.";
        }

        return documents.stream()
            .map(doc -> "---\n" + doc.getFormattedContent() + "\n---")
            .collect(Collectors.joining("\n\n"));
    }

    public ToolCallback toolCallback() {
        return FunctionToolCallback.builder("knowledge_retrieval", this)
            .description("检索知识库。当需要回答产品文档、配置、使用方法时调用。")
            .inputType(Request.class)
            .build();
    }

    public record Request(
        @JsonProperty(value = "query", required = true)
        @JsonPropertyDescription("搜索查询，包含关键术语")
        String query,

        @JsonProperty(value = "top_k")
        @JsonPropertyDescription("返回结果数量，默认 4")
        Integer topK
    ) {}
}
```

### Step 2：注册到 Agent

```java
@Bean
public ReactAgent ragAgent(KnowledgeRetrievalTool knowledgeTool) {
    return ReactAgent.builder()
        .chatClientBuilder(chatClientBuilder)
        .tools(knowledgeTool.toolCallback())  // 注册 RAG Tool
        .build();
}
```

### Step 3：Agent 智能调用

```
用户：Spring AI Alibaba 如何配置向量数据库？

Agent 思考：这个问题需要检索文档
  ↓
调用 knowledge_retrieval Tool
  ↓
返回相关文档片段
  ↓
Agent 基于文档生成答案
```

## Advisor 模式 vs Agent Tool 模式

| 对比项 | Advisor 模式 | Agent Tool 模式 |
|--------|-------------|----------------|
| 触发时机 | 每次调用自动触发 | Agent 智能决策 |
| 适用场景 | 固定知识域问答 | 多类型问题、智能客服 |
| 灵活性 | 低 | 高 |
| Token 消耗 | 每次都检索 | 按需检索 |

## 示例代码位置

- RAG Agent 示例：`examples/spring-ai-alibaba-agent-example/rag-agent-example/`
