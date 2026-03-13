# Spring AI Alibaba Integration 最佳实践

## 1. Agent 设计最佳实践

### 1.1 单一职责原则

每个 Agent 应该只负责一个特定领域：

```java
// 推荐：职责清晰的 Agent
@Bean
public ReactAgent dataAnalysisAgent(ChatModel chatModel) {
    return ReactAgent.builder()
        .name("data_analysis_agent")
        .description("数据分析智能体，专注于数据统计和趋势分析")
        .instruction("""
            你是一个数据分析专家。
            你的职责：
            1. 分析用户提供的数据
            2. 识别数据趋势和模式
            3. 提供数据驱动的建议
            """)
        .build();
}

// 不推荐：职责过多的 Agent
@Bean
public ReactAgent multiPurposeAgent(ChatModel chatModel) {
    return ReactAgent.builder()
        .name("everything_agent")
        .description("全能 Agent")  // 职责不清晰
        .instruction("你可以做任何事情...")  // 太宽泛
        .build();
}
```

### 1.2 明确的输入输出边界

```java
@Bean
public ReactAgent documentProcessorAgent(ChatModel chatModel) {
    return ReactAgent.builder()
        .name("document_processor")
        .description("文档处理智能体")
        .instruction("""
            输入：文档内容（文本格式）
            输出：结构化摘要
            
            处理流程：
            1. 读取文档内容
            2. 提取关键信息
            3. 生成结构化摘要
            """)
        .outputKey("document_summary")  // 明确输出键
        .build();
}
```

### 1.3 合理使用工具

```java
// 推荐：工具定义清晰
@Bean
public ToolCallback queryDatabaseTool() {
    return ToolCallback.builder()
        .name("query_database")
        .description("查询数据库获取业务数据，适用于需要精确数据的场景")
        .inputSchema("""
            {
                "type": "object",
                "properties": {
                    "table": {
                        "type": "string",
                        "description": "表名，如 orders, products, customers"
                    },
                    "conditions": {
                        "type": "array",
                        "description": "查询条件列表",
                        "items": {
                            "type": "object"
                        }
                    }
                },
                "required": ["table"]
            }
            """)
        .toolExecutor(this::executeQuery)
        .build();
}

// 不推荐：工具描述模糊
@Bean
public ToolCallback vagueTool() {
    return ToolCallback.builder()
        .name("do_something")  // 名称不清晰
        .description("做一些事情")  // 描述模糊
        .build();
}
```

---

## 2. A2A 通信最佳实践

### 2.1 服务注册配置

```yaml
spring:
  ai:
    alibaba:
      a2a:
        server:
          version: 1.0.0  # 使用语义化版本
          card:
            name: ${AGENT_NAME:my_agent}  # 支持环境变量
            description: 清晰描述 Agent 的能力
            capabilities:
              streaming: true
              push-notifications: false
            skills:
              - id: primary-skill
                name: 主要技能
                description: 详细描述技能的使用场景
```

### 2.2 超时和重试策略

```java
@Configuration
public class A2AResilienceConfig {
    
    @Bean
    public A2aClientConfig a2aClientConfig() {
        return A2aClientConfig.builder()
            .connectTimeout(Duration.ofSeconds(5))
            .readTimeout(Duration.ofSeconds(30))
            .writeTimeout(Duration.ofSeconds(10))
            .maxRetries(3)
            .retryBackoff(Duration.ofMillis(500))
            .build();
    }
    
    @Bean
    public CircuitBreaker a2aCircuitBreaker() {
        return CircuitBreaker.of("a2a", CircuitBreakerConfig.custom()
            .failureRateThreshold(50)
            .waitDurationInOpenState(Duration.ofSeconds(30))
            .slidingWindowSize(10)
            .build());
    }
}
```

### 2.3 错误处理

```java
@Service
public class RobustA2AClient {
    
    private final AgentCardProvider agentCardProvider;
    
    public Optional<String> invokeAgentSafely(String agentName, String input) {
        try {
            A2aRemoteAgent agent = A2aRemoteAgent.builder()
                .name(agentName)
                .agentCardProvider(agentCardProvider)
                .build();
                
            return agent.invoke(input)
                .flatMap(s -> s.value("output"))
                .map(Object::toString);
                
        } catch (AgentNotFoundException e) {
            log.warn("Agent not found: {}", agentName);
            return Optional.empty();
            
        } catch (AgentTimeoutException e) {
            log.error("Agent timeout: {}", agentName, e);
            throw new ServiceUnavailableException("Agent service unavailable");
            
        } catch (Exception e) {
            log.error("Unexpected error calling agent: {}", agentName, e);
            throw new AgentExecutionException("Agent execution failed", e);
        }
    }
}
```

---

## 3. 工作流节点最佳实践

### 3.1 节点命名规范

```java
// 推荐：使用语义化命名
StateGraph graph = new StateGraph(OverAllState.class)
    .addNode("validate_input", validateNode)      // 验证输入
    .addNode("preprocess_data", preprocessNode)   // 预处理数据
    .addNode("analyze_content", analyzeNode)      // 分析内容
    .addNode("generate_report", reportNode)       // 生成报告
    .addNode("validate_output", validateOutputNode); // 验证输出

// 不推荐：使用模糊命名
StateGraph graph = new StateGraph(OverAllState.class)
    .addNode("node1", node1)  // 名称无意义
    .addNode("node2", node2)
    .addNode("node3", node3);
```

### 3.2 状态管理

```java
// 推荐：使用明确的状态键
public class StateKeys {
    public static final String USER_INPUT = "user_input";
    public static final String PROCESSED_DATA = "processed_data";
    public static final String ANALYSIS_RESULT = "analysis_result";
    public static final String FINAL_OUTPUT = "final_output";
}

// 在节点中使用
@Override
public Map<String, Object> apply(OverAllState state) {
    String input = (String) state.value(StateKeys.USER_INPUT).orElse("");
    // 处理逻辑
    return Map.of(StateKeys.ANALYSIS_RESULT, result);
}
```

### 3.3 流式处理优化

```java
// 推荐：支持流式和批处理两种模式
public class OptimizedLlmNode implements NodeAction {
    
    @Override
    public Map<String, Object> apply(OverAllState state) {
        Boolean useStream = (Boolean) state.value("stream_mode").orElse(false);
        
        if (useStream) {
            // 流式处理，适合长时间任务
            Flux<ChatResponse> stream = buildStreamingResponse(state);
            return Map.of("streaming_output", stream);
        } else {
            // 批处理，适合快速响应
            ChatResponse response = buildBatchResponse(state);
            return Map.of("batch_output", response);
        }
    }
}
```

---

## 4. 性能优化建议

### 4.1 连接池配置

```yaml
# application.yml
spring:
  ai:
    alibaba:
      a2a:
        client:
          pool:
            max-connections: 100
            max-connections-per-route: 20
            connection-timeout: 5000
            read-timeout: 30000
```

### 4.2 缓存策略

```java
@Configuration
public class CacheConfig {
    
    @Bean
    public CacheManager agentCardCache() {
        return CaffeineCacheManager.builder()
            .cacheNames("agentCards")
            .initialCapacity(100)
            .maximumSize(500)
            .expireAfterWrite(Duration.ofMinutes(5))
            .build();
    }
}

// 使用缓存
@Service
public class CachedAgentCardProvider implements AgentCardProvider {
    
    @Cacheable(value = "agentCards", key = "#agentName")
    public AgentCard getAgentCard(String agentName) {
        // 从 Nacos 获取
        return nacosAgentCardProvider.getAgentCard(agentName);
    }
}
```

### 4.3 异步处理

```java
@Service
public class AsyncAgentService {
    
    private final ReactAgent agent;
    
    @Async("agentExecutor")
    public CompletableFuture<OverAllState> invokeAsync(String input) {
        return CompletableFuture.supplyAsync(() -> 
            agent.invoke(input).orElse(null)
        );
    }
}

@Configuration
class AsyncConfig {
    @Bean("agentExecutor")
    public Executor agentExecutor() {
        ThreadPoolTaskExecutor executor = new ThreadPoolTaskExecutor();
        executor.setCorePoolSize(5);
        executor.setMaxPoolSize(20);
        executor.setQueueCapacity(100);
        executor.setThreadNamePrefix("agent-");
        return executor;
    }
}
```

---

## 5. 安全最佳实践

### 5.1 敏感信息保护

```yaml
# 使用环境变量
spring:
  ai:
    dashscope:
      api-key: ${DASHSCOPE_API_KEY}  # 不要硬编码
    alibaba:
      a2a:
        nacos:
          username: ${NACOS_USERNAME}
          password: ${NACOS_PASSWORD}
```

### 5.2 输入验证

```java
@Service
public class InputValidator {
    
    public void validate(String input) {
        if (input == null || input.isBlank()) {
            throw new IllegalArgumentException("Input cannot be empty");
        }
        if (input.length() > 10000) {
            throw new IllegalArgumentException("Input too long");
        }
        // 防止注入攻击
        if (containsMaliciousContent(input)) {
            throw new SecurityException("Malicious content detected");
        }
    }
}
```

### 5.3 访问控制

```java
@Configuration
public class SecurityConfig {
    
    @Bean
    public SecurityFilterChain a2aSecurityFilterChain(HttpSecurity http) {
        return http
            .securityMatcher("/a2a/**", "/.well-known/**")
            .authorizeHttpRequests(auth -> auth
                .requestMatchers("/.well-known/agent.json").permitAll()
                .requestMatchers("/a2a/**").authenticated()
            )
            .oauth2ResourceServer(OAuth2ResourceServerConfigurer::jwt)
            .build();
    }
}
```

---

## 6. 可观测性最佳实践

### 6.1 日志规范

```java
@Slf4j
@Service
public class AgentService {
    
    public void process(String input) {
        MDC.put("traceId", generateTraceId());
        MDC.put("agentName", "my_agent");
        
        try {
            log.info("Processing request: {}", truncate(input, 100));
            // 处理逻辑
            log.info("Processing completed successfully");
        } catch (Exception e) {
            log.error("Processing failed", e);
            throw e;
        } finally {
            MDC.clear();
        }
    }
}
```

### 6.2 指标采集

```java
@Service
public class MetricsService {
    
    private final MeterRegistry meterRegistry;
    
    public void recordAgentExecution(String agentName, Duration duration, boolean success) {
        Timer.builder("agent.execution.duration")
            .tag("agent", agentName)
            .tag("success", String.valueOf(success))
            .register(meterRegistry)
            .record(duration);
            
        Counter.builder("agent.execution.count")
            .tag("agent", agentName)
            .tag("success", String.valueOf(success))
            .register(meterRegistry)
            .increment();
    }
}
```

---

## 7. 测试最佳实践

### 7.1 单元测试

```java
@ExtendWith(MockitoExtension.class)
class AgentServiceTest {
    
    @Mock
    private ChatModel chatModel;
    
    @InjectMocks
    private AgentService agentService;
    
    @Test
    void shouldProcessInputCorrectly() {
        // Given
        String input = "test input";
        when(chatModel.call(any())).thenReturn(mockResponse());
        
        // When
        Optional<OverAllState> result = agentService.process(input);
        
        // Then
        assertThat(result).isPresent();
        assertThat(result.get().value("output")).contains("expected output");
    }
}
```

### 7.2 集成测试

```java
@SpringBootTest
@Testcontainers
class A2AIntegrationTest {
    
    @Container
    static NacosContainer nacos = new NacosContainer("nacos/nacos-server:latest");
    
    @DynamicPropertySource
    static void configureNacos(DynamicPropertyRegistry registry) {
        registry.add("spring.ai.alibaba.a2a.nacos.server-addr", 
            () -> nacos.getHost() + ":" + nacos.getMappedPort(8848));
    }
    
    @Test
    void shouldRegisterAndDiscoverAgent() {
        // 测试注册和发现
    }
}
```

---

## 8. 部署最佳实践

### 8.1 健康检查

```java
@Component
public class AgentHealthIndicator implements HealthIndicator {
    
    private final AgentRegistry agentRegistry;
    
    @Override
    public Health health() {
        try {
            int activeAgents = agentRegistry.listAgents().size();
            return Health.up()
                .withDetail("activeAgents", activeAgents)
                .build();
        } catch (Exception e) {
            return Health.down()
                .withException(e)
                .build();
        }
    }
}
```

### 8.2 优雅关闭

```java
@Configuration
public class GracefulShutdownConfig {
    
    @Bean
    public GracefulShutdown gracefulShutdown() {
        return new GracefulShutdown(30, TimeUnit.SECONDS);
    }
    
    @PreDestroy
    public void onShutdown() {
        // 取消正在执行的任务
        // 保存状态
        // 关闭连接
    }
}
```

---

## 9. 常见反模式

### 9.1 避免过度嵌套

```java
// 不推荐：深度嵌套的条件边
graph.addConditionalEdge("node1", state -> {
    if (condition1) {
        if (condition2) {
            if (condition3) {
                return "node4";
            }
            return "node3";
        }
        return "node2";
    }
    return END;
});

// 推荐：扁平化处理
graph.addConditionalEdge("node1", state -> 
    determineNextNode(state)  // 独立方法处理逻辑
);

private String determineNextNode(OverAllState state) {
    if (condition1) return "node2";
    if (condition2) return "node3";
    if (condition3) return "node4";
    return END;
}
```

### 9.2 避免状态膨胀

```java
// 不推荐：存储过多数据
return Map.of(
    "original_input", largeInput,
    "intermediate_result", largeResult,
    "all_messages", allMessages,
    "debug_info", debugInfo
);

// 推荐：只存储必要数据
return Map.of(
    "output", finalResult,
    "status", "completed"
);
```

### 9.3 避免同步阻塞

```java
// 不推荐：在流式处理中阻塞
Flux<ChatResponse> stream = chatClient.stream();
List<ChatResponse> responses = stream.collectList().block();  // 阻塞

// 推荐：保持响应式
Flux<ChatResponse> stream = chatClient.stream();
return stream.map(this::processResponse);
```

---

## 10. 代码执行最佳实践

### 10.1 选择执行策略

**本地执行 (LocalCommandlineCodeExecutor)：**

- 适用于开发环境和受信任的代码
- 性能开销小，启动快
- 不提供隔离性，有安全风险

```java
CodeExecutor executor = new LocalCommandlineCodeExecutor();
CodeExecutionConfig config = new CodeExecutionConfig()
    .setWorkDir("./workspace")
    .setTimeout(60);
```

**Docker 执行 (DockerCodeExecutor)：**

- 适用于生产环境和不可信代码
- 提供隔离性和安全性
- 需要 Docker 环境支持

```java
CodeExecutor executor = new DockerCodeExecutor();
CodeExecutionConfig config = new CodeExecutionConfig()
    .setWorkDir("/app/workspace")
    .setDocker("python:3.11-slim")  // 指定镜像
    .setDockerHost("unix:///var/run/docker.sock")
    .setContainerName("code-exec-" + UUID.randomUUID())
    .setTimeout(600)
    .setMaxConnections(100)
    .setConnectionTimeout(30)
    .setResponseTimeout(50);
```

### 10.2 Docker 镜像选择

```java
// 推荐：使用精简镜像
.setDocker("python:3.11-slim")   // Python 执行
.setDocker("openjdk:17-jdk-slim") // Java 执行
.setDocker("node:18-alpine")      // Node.js 执行

// 不推荐：使用 full 镜像（体积大，攻击面大）
.setDocker("python:3.11")         // 包含不必要的工具
```

### 10.3 资源限制

```java
// 设置合理的超时和资源限制
CodeExecutionConfig config = new CodeExecutionConfig()
    .setTimeout(60)               // 60秒超时，防止无限循环
    .setWorkDir(UUID.randomUUID().toString())  // 独立工作目录
    .setContainerName("exec-" + sessionId);
```

### 10.4 工作目录管理

```java
// 推荐：为每次执行创建独立目录
String sessionId = UUID.randomUUID().toString();
String workDir = Paths.get("/app/workspace", sessionId).toString();

try {
    CodeExecutionConfig config = new CodeExecutionConfig()
        .setWorkDir(workDir);
    executor.executeCodeBlocks(codeBlocks, config);
} finally {
    // 清理工作目录
    FileUtils.deleteDirectory(new File(workDir));
}
```

### 10.5 多语言代码执行

```java
// 支持的语言
public enum CodeLanguage {
    PYTHON3,
    JAVA,
    JAVASCRIPT
}

// Python 执行示例
CodeBlock pythonCode = new CodeBlock("python", """
    import json
    data = {"result": 42}
    print(json.dumps(data))
    """);

// Java 执行示例（需要配置 classPath）
CodeBlock javaCode = new CodeBlock("java", """
    public class Main {
        public static void main(String[] args) {
            System.out.println("Hello from Java");
        }
    }
    """);
CodeExecutionConfig javaConfig = new CodeExecutionConfig()
    .setDocker("openjdk:17-jdk-slim")
    .setClassPath("/app/libs/*");  // 额外依赖
```

---

## 11. GraphAgentExecutor 使用最佳实践

### 11.1 流式响应配置

```java
// 客户端请求流式响应
MessageSendParams params = MessageSendParams.builder()
    .message(message)
    .metadata(Map.of(
        GraphAgentExecutor.STREAMING_METADATA_KEY, true,  // 启用流式
        "threadId", "session-123"  // 指定会话线程
    ))
    .build();
```

### 11.2 忽略的节点类型

GraphAgentExecutor 在流式输出中会过滤以下内部节点类型：

```java
// 以下节点类型的输出不会传递给客户端
IGNORE_NODE_TYPE = Set.of("preLlm", "postLlm", "preTool", "tool", "postTool");
```

这些是 Agent 内部处理节点，其输出主要用于调试，不需要传递给最终用户。

### 11.3 已知限制

| 限制项 | 说明 | 建议 |
|--------|------|------|
| cancel() 未实现 | 任务取消功能未实现 | 通过超时机制控制 |
| Agent 类型限制 | 仅支持 ReactAgent 和 A2aRemoteAgent | 确保根 Agent 是这两种类型 |
| 输出键检查 | 需要正确配置 outputKey | 使用 BaseAgent.getOutputKey() |

### 11.4 任务状态管理

```java
// 理解任务状态流转
TaskState.SUBMITTED   -> 任务已提交
TaskState.WORKING     -> 任务执行中
TaskState.COMPLETED   -> 任务完成
TaskState.CANCELED    -> 任务取消
TaskState.FAILED      -> 任务失败

// 任务会一直等待直到完成或取消
// 注意：cancel() 当前未实现，无法主动取消
```
