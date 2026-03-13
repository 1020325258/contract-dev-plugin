# Spring AI Alibaba Studio & Admin 最佳实践

## 1. Studio 最佳实践

### 1.1 AgentLoader 实现模式

#### 推荐：单一职责设计

```java
// 好的做法：每个 Agent 职责明确
@Component
public class MyAgentLoader implements AgentLoader {

    private final ChatClient chatClient;

    @Override
    public List<String> listAgents() {
        return List.of(
            "customer_service",    // 客服助手
            "code_reviewer",       // 代码审查
            "data_analyst"         // 数据分析
        );
    }

    @Override
    public Agent loadAgent(String name) {
        return switch (name) {
            case "customer_service" -> createCustomerServiceAgent();
            case "code_reviewer" -> createCodeReviewerAgent();
            case "data_analyst" -> createDataAnalystAgent();
            default -> throw new NoSuchElementException("Agent not found: " + name);
        };
    }
}
```

#### 反例：过于臃肿的 Agent

```java
// 不好的做法：一个 Agent 做所有事情
@Component
public class UniversalAgentLoader implements AgentLoader {

    @Override
    public List<String> listAgents() {
        return List.of("super_agent");  // 职责不清晰
    }

    @Override
    public Agent loadAgent(String name) {
        // 一个 Agent 包含所有功能，难以维护和测试
        return Agent.builder()
            .name("super_agent")
            .systemPrompt("你是一个万能助手...")  // 过于宽泛
            .tools(List.of(
                new CodeTool(),
                new DataTool(),
                new SearchTool(),
                new EmailTool(),
                // ... 太多工具
            ))
            .build();
    }
}
```

### 1.2 工具定义最佳实践

#### 推荐：明确的工具边界

```java
@Bean
public ToolCallback weatherTool(WeatherService weatherService) {
    return ToolCallback.builder()
        .name("get_weather")
        .description("获取指定城市的当前天气信息")
        .inputSchema("""
            {
              "type": "object",
              "properties": {
                "city": {
                  "type": "string",
                  "description": "城市名称，如：北京、上海"
                }
              },
              "required": ["city"]
            }
            """)
        .toolExecutor(args -> {
            String city = args.get("city").asText();
            return weatherService.getCurrentWeather(city);
        })
        .build();
}
```

#### 推荐：需要审批的敏感操作

```java
@Bean
public ToolCallback deleteFileTool() {
    return ToolCallback.builder()
        .name("delete_file")
        .description("删除指定路径的文件")
        .inputSchema("""
            {
              "type": "object",
              "properties": {
                "path": {"type": "string", "description": "文件路径"}
              },
              "required": ["path"]
            }
            """)
        .toolExecutor(this::deleteFile)
        .requiresConfirmation(true)  // 关键：敏感操作需要确认
        .build();
}
```

### 1.3 会话状态管理

#### 推荐：使用 Graph Core 持久化

```java
// 生产环境：使用数据库持久化
@Bean
public ThreadService threadService(DataSource dataSource) {
    return new DatabaseThreadService(dataSource);
}

// 或使用 Redis
@Bean
public ThreadService threadService(RedisTemplate<String, Object> redisTemplate) {
    return new RedisThreadService(redisTemplate);
}
```

#### 注意：默认实现是内存存储

```java
// ThreadServiceImpl 使用 ConcurrentHashMap
// 适用于开发测试，不适合生产环境
@Service
public class ThreadServiceImpl implements ThreadService {
    private final Map<String, Thread> threads = new ConcurrentHashMap<>();
    // ...
}
```

---

## 2. Admin 平台最佳实践

### 2.1 Prompt 管理最佳实践

#### 推荐：版本化 Prompt 管理

```
Prompt: customer-service-v1
├── v1.0 - 初始版本
├── v1.1 - 优化了问候语
├── v1.2 - 增加了产品知识
└── v2.0 - 重大改版（推荐使用）
```

#### 推荐：使用变量模板

```yaml
# Prompt 内容
你是一个专业的{{role}}，专门帮助用户解决{{domain}}问题。

请遵循以下原则：
1. 回答要{{tone}}
2. 如果不确定，请{{uncertain_action}}
3. 保持回答在{{max_length}}字以内

# 变量定义
variables:
  - name: role
    defaultValue: "客服专家"
  - name: domain
    defaultValue: "产品咨询"
  - name: tone
    defaultValue: "专业、友好"
  - name: uncertain_action
    defaultValue: "诚实地告知用户，并提供替代方案"
  - name: max_length
    defaultValue: "500"
```

#### 反例：硬编码 Prompt

```java
// 不好的做法：Prompt 硬编码在代码中
String prompt = "你是一个客服助手，请帮助用户解决问题...";
chatClient.prompt(prompt).call();
```

### 2.2 数据集管理最佳实践

#### 推荐：数据集分层设计

```
Dataset Hierarchy:
├── Training Dataset（训练集）
│   ├── 高质量标注数据
│   └── 领域专家审核
├── Validation Dataset（验证集）
│   ├── 用于 Prompt 调优
│   └── 定期更新
└── Test Dataset（测试集）
    ├── 用于最终评估
    └── 严格隔离，不参与调优
```

#### 推荐：从生产 Trace 创建数据集

```java
// 从生产环境收集真实用户问题
// 经人工审核后加入数据集
POST /api/dataset/from-trace
{
  "traceIds": ["trace-001", "trace-002"],
  "datasetName": "Production_QA_Quality",
  "requireReview": true
}
```

### 2.3 评估器设计最佳实践

#### 推荐：多维度评估

```java
@Component
public class CompositeEvaluator implements Evaluator {

    private final AccuracyEvaluator accuracyEvaluator;
    private final RelevanceEvaluator relevanceEvaluator;
    private final SafetyEvaluator safetyEvaluator;

    @Override
    public EvaluationResult evaluate(EvaluationContext context) {
        // 多维度评估
        double accuracy = accuracyEvaluator.evaluate(context).getScore();
        double relevance = relevanceEvaluator.evaluate(context).getScore();
        double safety = safetyEvaluator.evaluate(context).getScore();

        // 综合评分（加权平均）
        double overall = 0.4 * accuracy + 0.3 * relevance + 0.3 * safety;

        return EvaluationResult.builder()
            .score(overall)
            .details(Map.of(
                "accuracy", accuracy,
                "relevance", relevance,
                "safety", safety
            ))
            .build();
    }
}
```

### 2.4 工作流设计最佳实践

#### 推荐：使用 JudgeOperator 进行条件路由

```java
// 工作流配置示例
{
  "nodes": [
    {
      "type": "start",
      "name": "start"
    },
    {
      "type": "condition",
      "name": "check_intent",
      "conditions": [
        {
          "variable": "user_intent",
          "operator": "equals",        // 使用 JudgeOperator
          "value": "code_help",
          "nextNode": "code_assistant"
        },
        {
          "variable": "user_intent",
          "operator": "equals",
          "value": "general_chat",
          "nextNode": "chat_agent"
        }
      ]
    },
    {
      "type": "llm",
      "name": "code_assistant"
    },
    {
      "type": "llm",
      "name": "chat_agent"
    }
  ]
}
```

#### 可用的 JudgeOperator

| 操作符 | 适用类型 | 说明 |
|--------|----------|------|
| equals | string, number, boolean | 相等比较 |
| notEquals | string, number, boolean | 不等比较 |
| isNull | all | 空值检查 |
| isNotNull | all | 非空检查 |
| greater | number | 大于 |
| less | number | 小于 |
| contains | string, array, object | 包含检查 |
| lengthEquals | string, array | 长度等于 |

---

## 3. 性能优化建议

### 3.1 SSE 流式响应优化

```yaml
# application.yml
spring:
  mvc:
    async:
      request-timeout: 300000  # 5 分钟超时
server:
  servlet:
    encoding:
      charset: UTF-8
      enabled: true
      force: true
```

### 3.2 连接池优化

```yaml
# 数据库连接池
spring:
  datasource:
    hikari:
      maximum-pool-size: 20
      minimum-idle: 5
      connection-timeout: 30000
      idle-timeout: 600000

# Redis 连接池
spring:
  redis:
    lettuce:
      pool:
        max-active: 16
        max-idle: 8

# Elasticsearch
spring:
  elasticsearch:
    rest:
      connection-timeout: 5000
      read-timeout: 60000
```

### 3.3 缓存策略

```java
@Configuration
@EnableCaching
public class CacheConfig {

    @Bean
    public CacheManager cacheManager(RedisConnectionFactory factory) {
        RedisCacheManager.builder(factory)
            .cacheDefaults(RedisCacheConfiguration.defaultCacheConfig()
                .entryTtl(Duration.ofMinutes(30)))
            .build();
    }
}

// 缓存热门 Prompt
@Cacheable(value = "prompts", key = "#promptKey + ':' + #version")
public PromptVersion getPromptVersion(String promptKey, String version) {
    // ...
}
```

---

## 4. 安全最佳实践

### 4.1 API Key 管理

```yaml
# 推荐使用环境变量
spring:
  ai:
    dashscope:
      api-key: ${DASHSCOPE_API_KEY}

# 或使用 Vault
spring:
  cloud:
    vault:
      uri: https://vault.example.com
      token: ${VAULT_TOKEN}
```

### 4.2 工具权限控制

```java
@Bean
public ToolCallback sensitiveTool() {
    return ToolCallback.builder()
        .name("send_email")
        .description("发送邮件")
        .inputSchema("...")
        .toolExecutor(this::sendEmail)
        .requiresConfirmation(true)  // 需要用户确认
        .requiresRole("EMAIL_SENDER") // 需要特定角色
        .build();
}
```

### 4.3 日志脱敏

```java
@Aspect
@Component
public class SensitiveDataAspect {

    @Around("execution(* com.alibaba.cloud.ai..*Controller.*(..))")
    public Object maskSensitiveData(ProceedingJoinPoint pjp) throws Throwable {
        Object[] args = pjp.getArgs();
        // 对敏感数据进行脱敏处理
        for (int i = 0; i < args.length; i++) {
            if (args[i] instanceof String) {
                args[i] = maskApiKey((String) args[i]);
            }
        }
        return pjp.proceed(args);
    }
}
```

---

## 5. 可观测性最佳实践

### 5.1 完整的 OTel 配置

```yaml
management:
  otlp:
    tracing:
      export:
        enabled: true
      endpoint: http://otel-collector:4318/v1/traces
    metrics:
      export:
        enabled: true
  tracing:
    sampling:
      probability: 0.1  # 生产环境采样率 10%
  opentelemetry:
    resource-attributes:
      service:
        name: ${SERVICE_NAME:my-agent}
        version: ${SERVICE_VERSION:1.0.0}
      deployment:
        environment: ${DEPLOY_ENV:production}

spring:
  ai:
    chat:
      observations:
        log-prompt: true
        log-completion: true
```

### 5.2 自定义 Span

```java
@WithSpan("agent_execution")
public AgentResponse executeAgent(AgentRequest request) {
    Span.current().setAttribute("agent.name", request.getAgentName());
    Span.current().setAttribute("user.id", request.getUserId());

    // 业务逻辑
    return agentExecutor.execute(request);
}
```

---

## 6. 前端最佳实践

### 6.1 错误处理

```typescript
// StreamProvider.tsx
const processStream = async (stream: ReadableStream) => {
  try {
    const reader = stream.getReader();
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      const event = parseSSEEvent(value);
      if (event.error) {
        // 统一错误处理
        handleError(event.error);
      } else {
        updateMessages(event);
      }
    }
  } catch (error) {
    // 网络错误处理
    if (error instanceof NetworkError) {
      showToast('网络连接失败，请检查网络');
    } else {
      showToast('发生未知错误');
    }
  }
};
```

### 6.2 重连机制

```typescript
const connectWithRetry = async (maxRetries = 3) => {
  for (let i = 0; i < maxRetries; i++) {
    try {
      return await connectToBackend();
    } catch (error) {
      if (i === maxRetries - 1) throw error;
      await sleep(1000 * Math.pow(2, i)); // 指数退避
    }
  }
};
```
