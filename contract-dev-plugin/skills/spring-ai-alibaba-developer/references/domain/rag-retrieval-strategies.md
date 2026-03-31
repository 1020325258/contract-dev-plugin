# RAG 检索策略

## 概述
SAA 提供多种检索策略，适用于不同场景的检索需求。

## 检索策略对比

| 检索器 | 说明 | 适用场景 |
|--------|------|---------|
| `VectorStoreDocumentRetriever` | 纯向量检索 | 简单语义匹配 |
| `HybridElasticsearchRetriever` | 混合检索（向量 + BM25） | 需要关键词+语义检索 |
| `HyDeRetriever` | 假设文档嵌入检索 | 查询与文档表述差异大 |

## 向量检索

最基础的检索方式，通过语义相似度匹配文档。

```java
// 从 module-rag/ModuleRAGBasicController.java
RetrievalAugmentationAdvisor advisor = RetrievalAugmentationAdvisor.builder()
    .documentRetriever(
        VectorStoreDocumentRetriever.builder()
            .vectorStore(vectorStore)
            .similarityThreshold(0.50)  // 相似度阈值
            .build()
    )
    .build();

return chatClient.prompt()
    .advisors(advisor)
    .user(prompt)
    .call()
    .content();
```

## 混合检索（Hybrid Search）

结合向量检索和 BM25 关键词检索，提升检索精度。

```java
// 从 rag-component-example/RagComponentController.java
@Resource
private HybridElasticsearchRetriever hybridRetriever;

@GetMapping("/retrieval/hybrid")
public List<Document> retrievalHybrid() {
    Query query = Query.builder()
        .text("什么是hybridSearch")
        .build();
    return hybridRetriever.retrieve(query);
}

// 带过滤条件
@GetMapping("/retrieval/hybrid/filter")
public List<Document> retrievalHybridWithFilter() {
    FilterExpressionBuilder builder = new FilterExpressionBuilder();
    Filter.Expression expression = builder.or(
        builder.eq("category", "技术文档"),
        builder.eq("category", "HybridSearch")
    ).build();

    Map<String, Object> context = new HashMap<>();
    context.put(HybridElasticsearchRetriever.FILTER_EXPRESSION, expression);
    context.put(HybridElasticsearchRetriever.BM25_FILED, "metadata.word");

    Query query = Query.builder()
        .text("什么是hybridSearch")
        .context(context)
        .build();
    return hybridRetriever.retrieve(query);
}
```

## HyDE 检索（假设文档嵌入）

通过 LLM 生成假设文档，再用假设文档检索，解决查询与文档表述差异大的问题。

```java
// 从 rag-component-example/RagComponentController.java
@Resource
private HyDeRetriever hyDeRetriever;

@GetMapping("/retrieval/hyde")
public List<Document> retrievalHyde() {
    Query query = Query.builder()
        .text("什么是hybridSearch")
        .build();
    return hyDeRetriever.retrieve(query);
}
```

## Query 变换

### 查询重写

```java
QueryTransformer rewriteTransformer = RewriteQueryTransformer.builder()
    .chatClientBuilder(chatClientBuilder)
    .build();
```

### 查询压缩

```java
QueryTransformer compressionTransformer = CompressionQueryTransformer.builder()
    .chatClientBuilder(chatClientBuilder)
    .build();
```

### 查询翻译

```java
QueryTransformer translationTransformer = TranslationQueryTransformer.builder()
    .chatClientBuilder(chatClientBuilder)
    .targetLanguage("Chinese")
    .build();
```

### 查询扩展（MultiQuery）

```java
MultiQueryExpander multiQueryExpander = MultiQueryExpander.builder()
    .numberOfQueries(3)  // 生成 3 个相关查询
    .chatClientBuilder(chatClientBuilder)
    .build();
```

## HybridSearchAdvisor 组合使用

将多种检索策略组合使用：

```java
// 从 rag-component-example/RagComponentController.java
@GetMapping("/call/hybrid/advisor")
public Flux<ChatResponse> callHybridAdvisor(String message) {
    // 1. Query 变换
    List<QueryTransformer> queryTransformers = List.of(
        RewriteQueryTransformer.builder().chatClientBuilder(chatClientBuilder).build(),
        CompressionQueryTransformer.builder().chatClientBuilder(chatClientBuilder).build(),
        TranslationQueryTransformer.builder().chatClientBuilder(chatClientBuilder).targetLanguage("Chinese").build()
    );

    // 2. Query 扩展
    MultiQueryExpander multiQueryExpander = MultiQueryExpander.builder()
        .numberOfQueries(3)
        .chatClientBuilder(chatClientBuilder)
        .build();

    // 3. Rerank 后处理
    DashScopeRerankPostProcessor rerankProcessor = DashScopeRerankPostProcessor.builder()
        .rerankModel(rerankModel)
        .rerankOptions(dashScopeRerankProperties.getOptions())
        .build();

    // 4. 组装 HybridSearchAdvisor
    HybridSearchAdvisor hybridSearchAdvisor = HybridSearchAdvisor.builder()
        .queryTransformers(queryTransformers)
        .queryExpander(multiQueryExpander)
        .hyDeTransformer(hyDeTransformer)
        .hybridDocumentRetriever(hybridRetriever)
        .dashScopeRerankPostProcessor(rerankProcessor)
        .build();

    return chatClientBuilder.build()
        .prompt()
        .user(message)
        .advisors(hybridSearchAdvisor)
        .stream()
        .chatResponse();
}
```

## 示例代码位置

- 组件示例：`examples/spring-ai-alibaba-rag-example/rag-component-example/`
