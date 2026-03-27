# SAA Admin Agent 观测能力增强方案

## 概述

本文档介绍 Spring AI Alibaba Studio (SAA Admin) 中 Agent 运行期间的可观测能力增强方案，包含多种实现方案的对比和推荐实施路径。

## 背景

SAA Admin 已具备基础的可观测能力，但在 Agent 级别的细粒度观测方面存在不足。当前主要依赖 Spring AI 框架内置的观测能力，对于 Agent 执行过程中的详细信息（如 Tool 调用、ReAct 循环次数、知识检索详情）缺乏有效追踪手段。

## 核心内容

### 一、当前已具备的观测能力

| 层级 | 组件 | 能力 |
|------|------|------|
| 框架层 | Spring AI ChatModel | LLM 调用观测 (通过 ChatModelObservationConvention) |
| 框架层 | Spring AI ChatClient | 客户端调用观测 |
| 框架层 | Spring AI ToolCallback | 工具调用观测 (集成在 ChatClient 中) |
| 框架层 | Spring AI VectorStore | 向量检索观测 |
| 框架层 | Graph Core | Graph/Node/Edge 执行观测 (GraphObservationHandler) |
| 应用层 | SAA ObservabilityController | Trace 列表/详情/服务/概览查询 |
| 存储层 | Elasticsearch | Trace 数据存储和检索 |
| 导出层 | OTLP Exporter | 支持导出到 Jaeger/Zipkin 等 |

### 二、五种观测增强方案对比

#### 方案 1: Spring AI 内置 Observation (Level 1)

**原理**: 通过配置启用 Spring AI 已有的观测能力

**配置方式**:
```yaml
spring:
  ai:
    chat:
      observations:
        log-prompt: true      # 记录输入
        log-completion: true  # 记录输出
    chat-client:
      observations:
        log-prompt: true
```

**可观测内容**:
- ChatModel 调用: duration, prompt_tokens, completion_tokens, total_tokens
- Tool 调用: tool.name, tool.call.duration
- VectorStore 查询: vector.search.duration, vector.search.results

**优点**: 配置简单，无代码改动，自动覆盖所有 Spring AI 组件
**缺点**: 只能获取框架已有的观测点，无法添加自定义观测点

#### 方案 2: 自定义 Agent Observation (Level 2)

**原理**: 在 BasicAgentExecutor 中添加自定义 Observation

**实现方式**:
```java
// 在 BasicAgentExecutor 中
Observation agentObservation = Observation.createNotStarted("agent.execution", observationRegistry)
    .contextualName("agent:" + agentId)
    .lowCardinalityKeyValue("app_id", appId)
    .lowCardinalityKeyValue("agent_type", agentType)
    .start();
```

**可观测内容**:
- Agent 执行: duration, status (success/error)
- LLM 调用次数: llm.call.count (ReAct 循环次数)
- Tool 调用: tool.name, tool.call.count, tool.call.duration
- 知识检索: retrieval.kb_ids, retrieval.results_count, retrieval.duration
- Token 使用: prompt_tokens, completion_tokens

#### 方案 3: Graph Core Observation (Level 3)

**原理**: 如果使用 spring-ai-alibaba-graph-core 执行 Workflow，利用其内置观测

**已支持的观测**:
- Graph 开始/结束: GraphObservationHandler
- 节点执行: GraphNodeObservationHandler
- 边路由: GraphEdgeObservationHandler
- 指标生成: GraphMetricsGenerator

**配置方式**:
```yaml
spring:
  ai:
    graph:
      observation:
        enabled: true  # 默认启用
```

#### 方案 4: 自定义 Metrics + Prometheus (Level 4)

**原理**: 暴露自定义 Metrics 到 Prometheus，配合 Grafana 可视化

**实现方式**:
```java
Counter agentCallCounter = Counter.builder("agent.calls")
    .description("Agent 调用次数")
    .tag("app_id", appId)
    .register(meterRegistry);

Timer toolCallTimer = Timer.builder("agent.tool.call.duration")
    .description("Tool 调用耗时")
    .register(meterRegistry);
```

#### 方案 5: 完整 Trace 方案 (Level 5)

**原理**: 使用 OpenTelemetry API 添加自定义 Span

**实现方式**:
```java
Span span = tracer.spanBuilder("agent.execution")
    .setParent(Context.current())
    .setAttribute("app_id", appId)
    .startSpan();
```

### 三、方案对比总结

| 方案 | 复杂度 | 依赖 | 观测粒度 | 适用场景 |
|------|--------|------|---------|----------|
| Level 1: Spring AI 内置 | 配置 | 无 | 基础 | 快速启用 |
| Level 2: 自定义 Agent | 代码 | Micrometer | 中等 | 增强观测 |
| Level 3: Graph Core | 配置 | Graph Core | 中等 | Workflow |
| Level 4: Metrics | 部署 | Prometheus | 中等 | 监控告警 |
| Level 5: Full Trace | 代码+部署 | OTLP | 精细 | 全链路追踪 |

### 四、推荐实施路径

**阶段 1: 快速启用 (1-2 天)**
- 启用 Spring AI 内置 Observation 配置
- 验证 Elasticsearch 中的 Trace 数据
- 确认 SAA Admin ObservabilityController 可正常查询

**阶段 2: 增强 Agent 观测 (3-5 天)**
- 在 BasicAgentExecutor 中添加自定义 Observation
- 添加 Tool 调用详情（输入/输出）
- 添加 ReAct 循环次数统计

**阶段 3: 知识检索观测 (2-3 天)**
- 在 KnowledgeBaseRetrievalAdvisor 中添加观测
- 添加检索耗时、召回数量

**阶段 4: 生产级监控 (5-7 天)**
- 部署 Prometheus + Grafana
- 添加自定义 Metrics
- 配置告警规则

### 五、关键修改文件

- `spring-ai-alibaba-admin/.../core/agent/BasicAgentExecutor.java` - 添加 Agent 级别观测
- `spring-ai-alibaba-admin/.../core/rag/advisor/KnowledgeBaseRetrievalAdvisor.java` - 添加检索观测

### 六、参考实现

- `spring-ai-alibaba-graph-core/.../observation/graph/GraphObservationHandler.java` - Graph 观测示例
- `spring-boot-starters/.../GraphObservationAutoConfiguration.java` - 自动配置示例
- `spring-ai-alibaba-admin/.../service/client/*ChatClientFactory.java` - ChatClient 观测配置

## 注意事项

1. **Agent 级别观测缺失**: BasicAgentExecutor 中没有自定义 Observation，是当前主要改进点
2. **Tool 调用详情不足**: 只知道调用成功/失败，不清楚输入/输出
3. **ReAct 循环次数未知**: 无法追踪 Agent 推理轮次
4. **当前 SAA Admin 的 Workflow 未完全集成 Graph Core**

## 相关链接

- [Spring AI Observation 官方文档](https://docs.spring.io/spring-ai/reference/api/observation.html)
- [OpenTelemetry Java SDK](https://opentelemetry.io/docs/instrumentation/java/)
- [Graph Core 可观测性](./graph-core/best-practices.md)