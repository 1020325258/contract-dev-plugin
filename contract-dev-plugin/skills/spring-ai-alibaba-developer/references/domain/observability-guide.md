# 可观测性（Observability）

## 概述
SAA 基于 Spring Boot Actuator 和 Micrometer 提供完整的可观测性能力，支持 Zipkin、Langfuse、阿里云 ARMS 等后端。

## 模块结构

```
spring-ai-alibaba-observability-example/
├── observability-example/          # 基础可观测性（Zipkin）
├── observability-arms-example/     # 阿里云 ARMS 集成
├── observability-langfuse-example/ # Langfuse 集成
└── observationhandler-example/     # 自定义 Handler
```

## 配置项详解

```yaml
spring:
  ai:
    dashscope:
      observations:
        log-completion: true   # 记录响应
        log-prompt: true       # 记录提示词

    chat:
      client:
        observations:
          log-prompt: true
          log-completion: true
          include-error-logging: true

    vectorstore:
      observations:
        log-query-response: true  # 记录向量查询结果

    tools:
      observations:
        include-content: true     # 记录工具调用内容
```

## 后端集成

### Zipkin 集成

```yaml
management:
  tracing:
    sampling:
      probability: 1.0        # 采样率 100%
  zipkin:
    tracing:
      endpoint: http://localhost:9411/api/v2/spans
```

### Langfuse 集成（OTLP 协议）

```yaml
otel:
  service:
    name: spring-ai-alibaba-graph-langfuse
  traces:
    exporter: otlp
    sampler: always_on
  exporter:
    otlp:
      endpoint: "https://cloud.langfuse.com/api/public/otel"
      headers:
        Authorization: "Basic ${YOUR_BASE64_ENCODED_CREDENTIALS}"
      protocol: http/protobuf
```

## 自定义 ObservationHandler

```java
@Component
public class CustomerObservationHandler implements ObservationHandler<Observation.Context> {

    @Override
    public void onStart(Observation.Context context) {
        // 记录开始事件
    }

    @Override
    public void onStop(Observation.Context context) {
        // 记录结束事件，计算耗时
    }

    @Override
    public boolean supportsContext(Observation.Context context) {
        return true;
    }
}
```

## 示例代码位置

- 基础示例：`examples/spring-ai-alibaba-observability-example/observability-example/`
- Langfuse：`examples/spring-ai-alibaba-observability-example/observability-langfuse-example/`
