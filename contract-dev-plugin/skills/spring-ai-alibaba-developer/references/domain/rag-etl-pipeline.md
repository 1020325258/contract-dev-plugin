# RAG ETL Pipeline

## 概述
ETL Pipeline 负责文档的读取、转换和写入向量存储，是 RAG 系统的数据准备阶段。

## 架构图

```
┌─────────┐   ┌─────────────┐   ┌─────────┐
│ Reader  │ → │ Transformer │ → │ Writer  │
│ (读取)  │   │ (转换分割)   │   │ (写入)  │
└─────────┘   └─────────────┘   └─────────┘
```

## Reader 组件

| Reader | 用途 | 示例代码位置 |
|--------|------|-------------|
| `TextReader` | 纯文本文件 | `rag-etl-pipeline-example/ReaderController.java` |
| `JsonReader` | JSON 格式 | 同上 |
| `PagePdfDocumentReader` | PDF 按页分割 | 同上 |
| `ParagraphPdfDocumentReader` | PDF 按段落分割（适合有目录的 PDF） | 同上 |
| `MarkdownDocumentReader` | Markdown 文件 | 同上 |
| `JsoupDocumentReader` | HTML 网页 | 同上 |
| `TikaDocumentReader` | 通用格式（支持多种文档） | 同上 |

### Reader 使用示例

```java
// PDF 按页读取
Resource resource = new DefaultResourceLoader().getResource("classpath:/doc.pdf");
PagePdfDocumentReader reader = new PagePdfDocumentReader(resource);
List<Document> documents = reader.read();

// HTML 网页读取
JsoupDocumentReader htmlReader = new JsoupDocumentReader("https://example.com/doc");
List<Document> htmlDocs = htmlReader.read();

// 通用格式读取（Tika）
TikaDocumentReader tikaReader = new TikaDocumentReader(resource);
List<Document> tikaDocs = tikaReader.read();
```

## Transformer 组件

### TokenTextSplitter（文本分割）

```java
TokenTextSplitter splitter = TokenTextSplitter.builder()
    .withChunkSize(800)           // 目标 token 数
    .withMinChunkSizeChars(350)   // 最小字符数
    .withMinChunkLengthToEmbed(5) // 最小嵌入长度
    .withMaxNumChunks(10000)      // 最大块数
    .withKeepSeparator(true)      // 保留分隔符
    .build();

List<Document> splitDocs = splitter.split(documents);
```

### Metadata Enricher（元数据增强）

```java
// 关键词元数据增强
KeywordMetadataEnricher keywordEnricher = new KeywordMetadataEnricher(chatModel, 3);
List<Document> enriched = keywordEnricher.apply(documents);

// 摘要元数据增强（前后文摘要）
SummaryMetadataEnricher summaryEnricher = new SummaryMetadataEnricher(
    chatModel,
    List.of(NEXT, CURRENT, PREVIOUS)
);
List<Document> withSummary = summaryEnricher.apply(documents);
```

### ContentFormatTransformer（内容格式化）

```java
DefaultContentFormatter formatter = DefaultContentFormatter.defaultConfig();
ContentFormatTransformer transformer = new ContentFormatTransformer(formatter);
List<Document> formatted = transformer.apply(documents);
```

## 完整 ETL 流程

```java
// 从 rag-pgvector-example/RagPgVectorController.java
@GetMapping("/rag/importDocument")
public void importDocument() {
    // 1. 解析文档
    DocumentReader reader = new PagePdfDocumentReader(springAiResource);
    List<Document> documents = reader.get();

    // 2. 文本分割
    List<Document> splitDocuments = new TokenTextSplitter().apply(documents);

    // 3. 创建嵌入并存储到向量存储
    vectorStore.add(splitDocuments);
}
```

## 示例代码位置

- 完整 ETL 示例：`examples/spring-ai-alibaba-rag-example/rag-etl-pipeline-example/`
