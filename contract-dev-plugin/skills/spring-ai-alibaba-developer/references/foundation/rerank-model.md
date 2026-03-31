# 重排序模型（Rerank）

## 概述
Rerank 模型对向量检索返回的文档进行精确重排序，过滤低相关度文档，提升上下文质量。

## 为什么需要 Rerank？

| 问题 | 向量检索 | Rerank |
|------|---------|--------|
| **精度** | 近似搜索，可能遗漏 | 精确计算文档-查询相关性 |
| **语义理解** | 嵌入向量压缩语义 | 深度交叉编码，理解更精准 |
| **噪声过滤** | Top-K 中混入无关文档 | 过滤低相关度文档 |
| **Token 消耗** | 传入大量低质量上下文 | 传入少量高质量上下文 |

## 工作流程

```
Query
  ↓
┌─────────────┐
│ Vector Store│ → 返回 Top-K 文档（如 10-50 条）
│ 检索        │   可能包含相关度不高的文档
└─────────────┘
  ↓
┌─────────────┐
│ Rerank Model│ → 重新计算每篇文档与 Query 的精确相关性分数
│ 重排序      │   返回 Top-N 文档（如 3-5 条高相关度文档）
└─────────────┘
  ↓
高质量的上下文 → LLM 生成答案
```

## 使用方式

### 独立使用

```java
// 从 rag-component-example/RagComponentController.java
@GetMapping("/rerank/documents")
public List<Document> rerankDocuments() {
    // 1. 向量检索获取文档
    List<Document> retrievalDocuments = vectorStore.similaritySearch("什么是hybridSearch");

    // 2. Rerank 重排序
    DashScopeRerankPostProcessor rerankProcessor = DashScopeRerankPostProcessor.builder()
        .rerankModel(rerankModel)
        .rerankOptions(dashScopeRerankProperties.getOptions())
        .build();

    // 3. 返回重排序后的高质量文档
    return rerankProcessor.process(
        Query.builder().text("什么是hybridSearch").build(),
        retrievalDocuments
    );
}
```

### 与 RetrievalRerankAdvisor 结合

```java
// 从 rag-pgvector-example/RagPgVectorController.java
ChatClient.builder(chatModel)
    .defaultAdvisors(new RetrievalRerankAdvisor(
        vectorStore,      // 向量存储
        rerankModel,      // 重排序模型
        searchRequest,    // 搜索参数
        systemPromptTemplate,
        0.1               // 分数阈值，低于此值的文档被过滤
    ))
    .build()
    .prompt().user(message).stream().chatResponse();
```

## 核心组件

| 组件 | 说明 |
|------|------|
| `RerankModel` | 重排序模型接口 |
| `DashScopeRerankPostProcessor` | DashScope 重排序后处理器 |
| `RetrievalRerankAdvisor` | 集成检索+重排序的 Advisor |
