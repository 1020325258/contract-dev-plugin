# 模型评估（Evaluation）

## 概述
SAA 提供多种评估器用于评估 RAG 生成答案的质量，包括相关性、事实性、正确性、忠实度等维度。

## 评估器类型

| 评估器 | 来源 | 用途 | 输入 |
|--------|------|------|------|
| `RelevancyEvaluator` | Spring AI | 响应与上下文相关性 | query, context, response |
| `FactCheckingEvaluator` | Spring AI | 事实准确性（反幻觉） | document, claim |
| `AnswerRelevancyEvaluator` | SAA | 答案相关性评分 | question, truth_answer, student_answer |
| `AnswerCorrectnessEvaluator` | SAA | 答案正确性 | query, context, response |
| `AnswerFaithfulnessEvaluator` | SAA | 答案忠实度（无幻觉） | facts, student_answer |

## 评估维度

```
┌─────────────────────────────────────────────────────────────────┐
│                     RAG 评估维度                                 │
├─────────────────────────────────────────────────────────────────┤
│  1. 检索质量评估（Retrieval Quality）                            │
│  ├─ Recall@K: 召回率，正确文档是否被检索到                        │
│  ├─ MRR: 平均倒数排名，正确答案的排名位置                          │
│  └─ NDCG: 考虑排序位置的归一化折损累积增益                         │
│                                                                  │
│  2. 生成质量评估（Generation Quality）                           │
│  ├─ Relevancy: 回答是否与上下文相关                               │
│  ├─ Faithfulness: 回答是否忠实于上下文（无幻觉）                   │
│  └─ Correctness: 回答是否正确回答问题                             │
└─────────────────────────────────────────────────────────────────┘
```

## 使用方式

### 基础用法

```java
// 1. 创建评估器
Evaluator evaluator = RelevancyEvaluator.builder()
    .chatClientBuilder(chatClientBuilder)
    .build();

// 2. 构建评估请求
EvaluationRequest request = new EvaluationRequest(
    query,      // 用户查询
    context,    // 检索到的上下文文档
    response    // AI 生成的响应
);

// 3. 执行评估
EvaluationResponse response = evaluator.evaluate(request);
boolean pass = response.isPass();  // 是否通过评估
```

### 完整评估流程

```java
// 从 evaluation-example/EvaluationController.java
@GetMapping("/sa/relevancy")
public String evaluateRelevancy(@RequestParam String query) {
    // 1. RAG 生成
    var chatResponse = chatClient
        .prompt()
        .advisors(ragAdvisor)
        .user(query)
        .call()
        .chatResponse();

    List<Document> context = chatResponse.getMetadata()
        .get(RetrievalAugmentationAdvisor.DOCUMENT_CONTEXT);
    String response = chatResponse.getResult().getOutput().getText();

    // 2. 评估
    var evaluator = RelevancyEvaluator.builder()
        .chatClientBuilder(chatClientBuilder)
        .build();

    var request = new EvaluationRequest(query, context, response);
    boolean pass = evaluator.evaluate(request).isPass();

    // 3. 根据评估结果处理
    return pass ? response : "暂无数据";
}
```

## 评估器原理

### RelevancyEvaluator

用 LLM 判断回答是否与上下文相关：

```
Prompt:
Your task is to evaluate if the response for the query
is in line with the context information provided.

You have two options to answer. Either YES or NO.

Query: {query}
Response: {response}
Context: {context}

Answer: YES/NO
```

### FactCheckingEvaluator

用 LLM 验证回答是否符合上下文事实（反幻觉）：

```
Prompt:
Evaluate whether or not the following claim is supported by the provided document.
Respond with "yes" if the claim is supported, or "no" if it is not.

Document: {document}
Claim: {claim}
```

## 示例代码位置

- 完整示例：`examples/spring-ai-alibaba-evaluation-example/`
