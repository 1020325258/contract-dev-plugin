# Spring AI Alibaba Integration 功能开发指南

## 1. 快速开始

### 1.1 环境要求

- JDK 17+
- Maven 3.6+
- Nacos 3.x (用于 A2A 服务发现)
- Spring Boot 3.5.x

### 1.2 依赖引入

```xml
<!-- pom.xml -->
<dependencies>
    <!-- 核心依赖 -->
    <dependency>
        <groupId>com.alibaba.cloud.ai</groupId>
        <artifactId>spring-ai-alibaba-starter-a2a-nacos</artifactId>
    </dependency>
    
    <!-- 内置节点 -->
    <dependency>
        <groupId>com.alibaba.cloud.ai</groupId>
        <artifactId>spring-ai-alibaba-starter-builtin-nodes</artifactId>
    </dependency>
    
    <!-- Nacos 动态配置 (可选) -->
    <dependency>
        <groupId>com.alibaba.cloud.ai</groupId>
        <artifactId>spring-ai-alibaba-starter-config-nacos</artifactId>
    </dependency>
    
    <!-- 可观测性 (可选) -->
    <dependency>
        <groupId>com.alibaba.cloud.ai</groupId>
        <artifactId>spring-ai-alibaba-starter-graph-observation</artifactId>
    </dependency>
</dependencies>
```

---

## 2. A2A Nacos 集成开发

### 2.1 基础配置

```yaml
# application.yml
server:
  port: 8080

spring:
  application:
    name: my-agent-service
  ai:
    dashscope:
      api-key: ${DASHSCOPE_API_KEY}
      chat:
        options:
          model: qwen-plus
    alibaba:
      a2a:
        nacos:
          server-addr: ${NACOS_SERVER_ADDR:127.0.0.1:8848}
          username: ${NACOS_USERNAME:nacos}
          password: ${NACOS_PASSWORD:nacos}
          namespace: public
          discovery:
            enabled: true    # 启用服务发现
          registry:
            enabled: true    # 启用服务注册
        server:
          version: 1.0.0
          card:
            name: my_agent
            description: 我的智能体服务
            provider:
              name: My Organization
              url: https://my-org.com
```

### 2.2 创建 Agent 服务提供者

```java
@Configuration
public class AgentConfig {

    @Bean(name = "myAgent")
    public ReactAgent myAgent(ChatModel chatModel) {
        return ReactAgent.builder()
            .name("my_agent")
            .model(chatModel)
            .description("我的智能体服务")
            .instruction("你是一个专业的助手，负责处理用户请求。")
            .outputKey("messages")
            .build();
    }
    
    @Bean
    public AgentLoader agentLoader(@Qualifier("myAgent") ReactAgent myAgent) {
        return new AgentLoader() {
            @Override
            @Nonnull
            public List<String> listAgents() {
                return List.of(myAgent.name());
            }

            @Override
            public Agent loadAgent(String name) {
                if (myAgent.name().equals(name)) {
                    return myAgent;
                }
                throw new NoSuchElementException("Agent not found: " + name);
            }
        };
    }
}
```

### 2.3 创建 Agent 服务消费者

```java
@Service
public class AgentClientService {

    private final AgentCardProvider agentCardProvider;
    
    public AgentClientService(AgentCardProvider agentCardProvider) {
        this.agentCardProvider = agentCardProvider;
    }
    
    public String callRemoteAgent(String agentName, String input) {
        // 创建远程代理
        A2aRemoteAgent remoteAgent = A2aRemoteAgent.builder()
            .name(agentName)
            .agentCardProvider(agentCardProvider)
            .description("远程 Agent 调用")
            .instruction("{input}")
            .build();
        
        // 调用远程 Agent
        Optional<OverAllState> result = remoteAgent.invoke(input);
        
        return result.flatMap(s -> s.value("output"))
            .map(Object::toString)
            .orElse("No response");
    }
}
```

### 2.4 REST API 使用

启动服务后，可以通过以下方式访问：

```bash
# 获取 AgentCard
curl http://localhost:8080/.well-known/agent.json

# 发送消息
curl -X POST http://localhost:8080/message \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "send_message",
    "params": {
      "message": {
        "role": "user",
        "content": "你好，请帮我分析一下数据"
      }
    },
    "id": "req-001"
  }'
```

---

## 3. 内置节点使用

### 3.1 LlmNode 使用

```java
@Service
public class WorkflowService {

    private final ChatClient chatClient;
    
    public WorkflowService(ChatClient.Builder chatClientBuilder) {
        this.chatClient = chatClientBuilder.build();
    }
    
    public LlmNode createLlmNode() {
        return LlmNode.builder()
            .chatClient(chatClient)
            .systemPromptTemplate("你是一个专业的{role}。")
            .userPromptTemplate("请分析以下数据：{data}")
            .params(Map.of(
                "role", "数据分析师",
                "data", "销售数据..."
            ))
            .outputKey("analysis_result")
            .stream(false)  // 非流式
            .build();
    }
    
    // 流式 LlmNode
    public LlmNode createStreamingLlmNode() {
        return LlmNode.builder()
            .chatClient(chatClient)
            .systemPromptTemplate("你是一个助手。")
            .userPromptTemplate("{input}")
            .messagesKey("history_messages")  // 从 State 获取消息
            .outputKey("streaming_response")
            .stream(true)  // 流式
            .build();
    }
}
```

### 3.2 ToolNode 使用

```java
@Configuration
public class ToolConfig {
    
    @Bean
    public ToolCallback weatherTool() {
        return ToolCallback.builder()
            .name("get_weather")
            .description("获取指定城市的天气信息")
            .inputSchema("""
                {
                    "type": "object",
                    "properties": {
                        "city": {
                            "type": "string",
                            "description": "城市名称"
                        }
                    },
                    "required": ["city"]
                }
                """)
            .toolExecutor((toolInput) -> {
                String city = (String) toolInput.get("city");
                return "城市 " + city + " 今天晴，温度 25°C";
            })
            .build();
    }
    
    @Bean
    public ToolNode weatherToolNode(ToolCallback weatherTool) {
        return new ToolNode(weatherTool);
    }
}
```

### 3.3 AgentNode 使用

```java
@Service
public class MultiAgentService {

    private final ChatModel chatModel;
    
    public MultiAgentService(ChatModel chatModel) {
        this.chatModel = chatModel;
    }
    
    public AgentNode createSubAgentNode() {
        // 创建子 Agent
        ReactAgent subAgent = ReactAgent.builder()
            .name("sub_agent")
            .model(chatModel)
            .instruction("你是一个专家助手。")
            .outputKey("sub_result")
            .build();
        
        return new AgentNode(subAgent);
    }
}
```

### 3.4 HumanNode 使用

```java
@Service
public class HumanInteractionService {
    
    public HumanNode createHumanNode() {
        return HumanNode.builder()
            .question("请确认是否继续执行？(yes/no)")
            .inputKey("user_confirmation")
            .timeout(Duration.ofMinutes(5))
            .build();
    }
}
```

### 3.5 CodeExecutorNodeAction 使用

```java
@Service
public class CodeExecutionService {
    
    public CodeExecutorNodeAction createPythonCodeNode() {
        return CodeExecutorNodeAction.builder()
            .codeExecutor(new LocalCommandlineCodeExecutor())
            .language(CodeLanguage.PYTHON3)
            .codeTemplate("""
                import json
                data = {{input_data}}
                result = process_data(data)
                print(json.dumps(result))
                """)
            .build();
    }
    
    public CodeExecutorNodeAction createDockerCodeNode() {
        CodeExecutionConfig config = CodeExecutionConfig.builder()
            .image("python:3.11-slim")
            .timeout(Duration.ofSeconds(30))
            .build();
            
        return CodeExecutorNodeAction.builder()
            .codeExecutor(new DockerCodeExecutor(config))
            .language(CodeLanguage.PYTHON3)
            .build();
    }
}
```

### 3.6 构建完整工作流

```java
@Service
public class WorkflowBuilderService {

    private final ChatClient chatClient;
    
    public CompiledGraph buildAnalysisWorkflow() {
        // 1. 创建节点
        LlmNode analysisNode = LlmNode.builder()
            .chatClient(chatClient)
            .systemPromptTemplate("你是数据分析师。")
            .userPromptTemplate("分析：{input}")
            .outputKey("analysis")
            .build();
            
        HumanNode confirmNode = HumanNode.builder()
            .question("分析结果是否满意？")
            .inputKey("satisfaction")
            .build();
            
        LlmNode refineNode = LlmNode.builder()
            .chatClient(chatClient)
            .systemPromptTemplate("根据用户反馈优化分析。")
            .userPromptTemplate("原分析：{analysis}\n反馈：{satisfaction}")
            .outputKey("refined_analysis")
            .build();
        
        // 2. 构建状态图
        StateGraph graph = new StateGraph(OverAllState.class)
            .addNode("analyze", analysisNode)
            .addNode("confirm", confirmNode)
            .addNode("refine", refineNode)
            .addEdge(START, "analyze")
            .addEdge("analyze", "confirm")
            .addConditionalEdge("confirm", state -> {
                String satisfaction = (String) state.value("satisfaction").orElse("");
                return satisfaction.contains("yes") ? END : "refine";
            })
            .addEdge("refine", END);
        
        // 3. 编译
        return graph.compile();
    }
}
```

---

## 4. Nacos 动态配置

### 4.1 基础配置

```yaml
# application.yml
spring:
  ai:
    alibaba:
      agent:
        proxy:
          nacos:
            enabled: true
            server-addr: ${NACOS_SERVER_ADDR:127.0.0.1:8848}
            namespace: public
            group: DEFAULT_GROUP
            data-id: agent-config.yaml
            agent-name: dynamic_agent
            prompt-key: my_prompt
```

### 4.2 Nacos 配置内容

```yaml
# Nacos Data ID: agent-config.yaml
agent:
  name: dynamic_agent
  description: 动态配置的智能体
  
  model:
    provider: dashscope
    name: qwen-plus
    options:
      temperature: 0.7
      
  prompt:
    system: |
      你是一个动态配置的智能体。
      可以根据 Nacos 配置实时更新行为。
      
  mcp-servers:
    - name: tools-server
      url: http://tools-server:8080/mcp
```

### 4.3 使用动态配置

```java
@Service
public class DynamicAgentService {

    private final NacosAgentBuilderFactory agentBuilderFactory;
    
    public DynamicAgentService(NacosAgentBuilderFactory agentBuilderFactory) {
        this.agentBuilderFactory = agentBuilderFactory;
    }
    
    public ReactAgent createDynamicAgent() {
        // 从 Nacos 配置构建 Agent
        return agentBuilderFactory.createBuilder()
            .build();
    }
}
```

---

## 5. 可观测性集成

### 5.1 基础配置

```yaml
# application.yml
spring:
  ai:
    alibaba:
      graph:
        observation:
          enabled: true

management:
  observations:
    enabled: true
  tracing:
    enabled: true
    sampling:
      probability: 1.0
  endpoints:
    web:
      exposure:
        include: prometheus, health, info, metrics

# OpenTelemetry 配置
otel:
  exporter:
    otlp:
      endpoint: http://localhost:4317
  traces:
    exporter: otlp
  metrics:
    exporter: otlp
```

### 5.2 自定义观测指标

```java
@Configuration
public class ObservationConfig {
    
    @Bean
    public ChatModelObservationConvention customChatModelObservationConvention() {
        return new ChatModelObservationConvention() {
            @Override
            public String getName() {
                return "spring.ai.alibaba.chat.model";
            }
            
            @Override
            public String getContextualName(ChatModelObservationContext context) {
                return "alibaba.chat." + context.getOperationMetadata().getModel();
            }
        };
    }
}
```

---

## 6. 最佳实践

### 6.1 Agent 设计原则

1. **单一职责**: 每个 Agent 只负责一个特定领域
2. **明确边界**: 清晰定义 Agent 的输入输出
3. **可观测**: 为关键操作添加观测点
4. **容错设计**: 处理超时、重试、降级

### 6.2 A2A 通信优化

```java
// 连接池配置
@Bean
public WebClient a2aWebClient() {
    return WebClient.builder()
        .clientConnector(new ReactorClientHttpConnector(
            HttpClient.create()
                .responseTimeout(Duration.ofSeconds(30))
                .option(ChannelOption.CONNECT_TIMEOUT_MILLIS, 5000)
        ))
        .build();
}

// 重试策略
@Bean
public Retry a2aRetry() {
    return Retry.backoff(3, Duration.ofMillis(500))
        .filter(e -> e instanceof WebClientRequestException);
}
```

### 6.3 节点组合模式

```java
// 链式组合
public class ChainedNodes {
    
    public static List<NodeAction> createChain(ChatClient chatClient) {
        return List.of(
            LlmNode.builder()
                .chatClient(chatClient)
                .systemPromptTemplate("分析输入")
                .outputKey("analysis")
                .build(),
                
            TemplateTransformNode.builder()
                .template("分析结果：{analysis}")
                .outputKey("formatted")
                .build(),
                
            AnswerNode.builder()
                .outputKey("final_answer")
                .build()
        );
    }
}
```

### 6.4 错误处理

```java
@Service
public class RobustAgentService {

    public Optional<OverAllState> safeInvoke(ReactAgent agent, String input) {
        try {
            return agent.invoke(input);
        } catch (GraphRunnerException e) {
            log.error("Agent execution failed", e);
            return Optional.empty();
        } catch (Exception e) {
            log.error("Unexpected error", e);
            throw new AgentExecutionException("Agent failed", e);
        }
    }
    
    public Flux<OverAllState> safeStream(ReactAgent agent, String input) {
        return agent.stream(input)
            .onErrorResume(e -> {
                log.error("Streaming failed", e);
                return Flux.empty();
            });
    }
}
```
