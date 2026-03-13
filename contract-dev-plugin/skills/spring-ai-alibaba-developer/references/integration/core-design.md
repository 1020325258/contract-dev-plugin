# Spring AI Alibaba Integration 核心设计分析

## 1. A2A 协议设计

### 1.1 协议概述

A2A (Agent-to-Agent) 是 Spring AI Alibaba 实现的 Agent 间通信协议，支持 Agent 之间的发现、调用和协作。协议基于 JSON-RPC 2.0 规范实现。

### 1.2 核心组件架构

```
┌─────────────────────────────────────────────────────────────┐
│                      A2A Client                              │
│  ┌─────────────────┐    ┌─────────────────────────────────┐ │
│  │ AgentCardProvider│───▶│ NacosAgentCardProvider         │ │
│  └─────────────────┘    │ (从 Nacos 发现 AgentCard)       │ │
│                         └─────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      Nacos Registry                          │
│  ┌─────────────────────────────────────────────────────────┐│
│  │  AgentCard 存储                                          ││
│  │  - Agent 名称、描述、能力                                ││
│  │  - 服务地址、端口                                        ││
│  │  - API 端点定义                                          ││
│  └─────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      A2A Server                              │
│  ┌─────────────────┐    ┌─────────────────────────────────┐ │
│  │ JsonRpcA2a     │───▶│ GraphAgentExecutor              │ │
│  │ RequestHandler │    │ (执行 ReactAgent/A2aRemoteAgent)│ │
│  └─────────────────┘    └─────────────────────────────────┘ │
│           │                                                  │
│           ▼                                                  │
│  ┌─────────────────────────────────────────────────────────┐│
│  │ RouterFunction (Spring WebFlux)                         ││
│  │ - /.well-known/agent.json (AgentCard 端点)              ││
│  │ - /message (消息处理端点)                                ││
│  └─────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────┘
```

### 1.3 AgentCard 结构

AgentCard 是 A2A 协议的核心概念，描述了 Agent 的能力和访问方式：

```java
// AgentCard 核心属性
public class AgentCard {
    // Agent 标识
    private String name;           // Agent 名称
    private String description;    // Agent 描述
    private String version;        // 版本号

    // 能力定义
    private List<Capability> capabilities;  // Agent 能力列表

    // 服务端点
    private String url;            // 服务地址
    private Integer port;          // 服务端口

    // 传输类型
    private String type;           // JSON_RPC 或 GRPC
}
```

### 1.4 请求处理流程

```
Client Request (JSON-RPC)
        │
        ▼
┌───────────────────────────────┐
│ JsonRpcA2aRequestHandler      │
│ - 解析请求类型                │
│ - 区分流式/非流式请求         │
└───────────────────────────────┘
        │
        ├──▶ 非流式请求
        │    ├── GetTaskRequest
        │    ├── SendMessageRequest
        │    ├── CancelTaskRequest
        │    └── PushNotificationConfig 相关
        │
        └──▶ 流式请求
             ├── SendStreamingMessageRequest
             └── TaskResubscriptionRequest
                    │
                    ▼
        ┌───────────────────────────────┐
        │ GraphAgentExecutor            │
        │ - 注入流式元数据              │
        │ - 调用底层 Agent              │
        │ - 返回 Flux<JSONRPCResponse>  │
        └───────────────────────────────┘
```

---

## 2. Nacos 服务发现机制

### 2.1 服务注册流程

```java
// NacosAgentRegistry.java
public class NacosAgentRegistry implements AgentRegistry {

    @Override
    public void register(AgentCard agentCard) {
        // 通过 NacosA2aOperationService 注册 Agent
        a2aOperationService.registerAgent(agentCard);
    }
}
```

### 2.2 配置属性映射

```yaml
# application.yml
spring:
  ai:
    alibaba:
      a2a:
        nacos:
          namespace: public                    # 命名空间
          server-addr: 127.0.0.1:8848         # Nacos 服务地址
          username: nacos                      # 用户名
          password: nacos                      # 密码
          discovery:
            enabled: true                      # 启用服务发现
```

对应的 Properties 类：

```java
@ConfigurationProperties(prefix = "spring.ai.alibaba.a2a.nacos")
public class NacosA2aProperties {
    String namespace = "public";
    String serverAddr;
    String username;
    String password;
    String accessKey;
    String secretKey;
    String endpoint;

    // 转换为 Nacos Properties
    public Properties getNacosProperties() {
        Properties properties = new Properties();
        properties.put(PropertyKeyConst.NAMESPACE, namespace);
        properties.put(PropertyKeyConst.SERVER_ADDR, serverAddr);
        // ...
        return properties;
    }
}
```

### 2.3 服务发现自动配置

```java
@AutoConfiguration(before = { A2aClientAgentCardProviderAutoConfiguration.class })
@ConditionalOnClass({ A2aClientAgentCardProviderAutoConfiguration.class })
@EnableConfigurationProperties({ NacosA2aProperties.class })
@ConditionalOnProperty(prefix = NacosA2aProperties.PREFIX,
    value = "discovery.enabled", havingValue = "true", matchIfMissing = true)
public class NacosA2aDiscoveryAutoConfiguration {

    @Bean
    @ConditionalOnMissingBean
    public A2aService a2aService(NacosA2aProperties nacosA2aProperties)
        throws NacosException {
        return AiFactory.createAiService(nacosA2aProperties.getNacosProperties());
    }

    @Bean
    public NacosAgentCardProvider nacosAgentCardProvider(A2aService a2aService)
        throws Exception {
        return new NacosAgentCardProvider(a2aService);
    }
}
```

---

## 3. 可观测性集成设计

### 3.1 架构设计

```
┌─────────────────────────────────────────────────────────────┐
│                   Application Layer                          │
│  ┌─────────────────────────────────────────────────────────┐│
│  │  Agent Execution                                         ││
│  │  - ReactAgent                                            ││
│  │  - Graph Workflow                                        ││
│  └─────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                  Observation Layer                           │
│  ┌─────────────────────────────────────────────────────────┐│
│  │  Micrometer ObservationRegistry                          ││
│  │  - ChatModelObservationConvention                       ││
│  │  - ChatClientObservationConvention                      ││
│  └─────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   Exporter Layer                             │
│  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐   │
│  │ Prometheus    │  │ Zipkin/Jaeger │  │ OTLP          │   │
│  └───────────────┘  └───────────────┘  └───────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### 3.2 自动配置

```java
@AutoConfiguration
@EnableConfigurationProperties({ GraphObservationProperties.class })
public class GraphObservationAutoConfiguration {

    @Bean
    @ConditionalOnMissingBean
    public SpringAiAlibabaChatModelObservationConvention
        chatModelObservationConvention() {
        return new SpringAiAlibabaChatModelObservationConvention();
    }
}
```

### 3.3 配置属性

```yaml
# application.yml
spring:
  ai:
    alibaba:
      graph:
        observation:
          enabled: true
          # 其他观察配置
management:
  observations:
    enabled: true
  tracing:
    enabled: true
  endpoints:
    web:
      exposure:
        include: prometheus, health, info
```

---

## 4. 内置节点设计

### 4.1 NodeAction 接口

所有内置节点实现统一的 `NodeAction` 接口：

```java
public interface NodeAction {
    Map<String, Object> apply(OverAllState state) throws Exception;
}
```

### 4.2 LlmNode 设计

LlmNode 是最核心的节点，封装了 LLM 调用逻辑：

```java
public class LlmNode implements NodeAction {

    // Prompt 配置
    private String systemPrompt;
    private String userPrompt;
    private Map<String, Object> params;

    // 消息配置
    private List<Message> messages;
    private String messagesKey;      // 从 State 获取消息的 key

    // 工具配置
    private List<ToolCallback> toolCallbacks;
    private List<Advisor> advisors;

    // 输出配置
    private String outputKey;
    private String outputSchema;     // 结构化输出 Schema

    // 流式支持
    private Boolean stream = Boolean.FALSE;

    @Override
    public Map<String, Object> apply(OverAllState state) throws Exception {
        initNodeWithState(state);  // 从 State 初始化配置

        if (Boolean.TRUE.equals(stream)) {
            Flux<ChatResponse> chatResponseFlux = stream(state);
            return Map.of(outputKey != null ? outputKey : "messages", chatResponseFlux);
        } else {
            ChatResponse response = call(state);
            AssistantMessage output = response.getResult().getOutput();
            return Map.of("messages", output);
        }
    }
}
```

### 4.3 节点状态管理

节点通过 `OverAllState` 管理工作流状态：

```java
// 从 State 获取配置
private void initNodeWithState(OverAllState state) {
    // 从 State 获取 userPrompt
    if (StringUtils.hasLength(userPromptKey)) {
        this.userPrompt = (String) state.value(userPromptKey).orElse(this.userPrompt);
    }

    // 从 State 获取 messages
    if (StringUtils.hasLength(messagesKey)) {
        Object messagesValue = state.value(messagesKey).orElse(null);
        if (messagesValue != null) {
            this.messages = convertToMessages(messagesValue);
        }
    }

    // 渲染 Prompt 模板
    if (StringUtils.hasLength(userPrompt) && !params.isEmpty()) {
        this.userPrompt = renderPromptTemplate(userPrompt, params);
    }
}
```

---

## 5. 配置热更新机制

### 5.1 Nacos 配置集成

```java
@Component
@ConditionalOnProperty(name = "spring.ai.alibaba.agent.proxy.nacos.enabled",
    havingValue = "true", matchIfMissing = true)
public class NacosAgentConfig {

    @Bean
    public Properties nacosAgentProxyProperties(ConfigurableEnvironment environment) {
        Properties props = new Properties();
        String prefix = "spring.ai.alibaba.agent.proxy.nacos.";

        // 收集所有相关配置
        Set<String> propertyNames = environment.getPropertySources().stream()
            .filter(ps -> ps instanceof EnumerablePropertySource)
            .flatMap(ps -> Arrays.stream(
                ((EnumerablePropertySource<?>) ps).getPropertyNames()))
            .filter(name -> name.startsWith(prefix))
            .collect(Collectors.toSet());

        propertyNames.forEach(name -> {
            String value = environment.getProperty(name);
            if (value != null) {
                props.setProperty(name.substring(prefix.length()), value);
            }
        });

        return props;
    }
}
```

### 5.2 Agent 配置注入器

```java
// 模型注入器
public class NacosModelInjector implements NacosAgentInjector {
    @Override
    public void inject(ReactAgent.Builder builder, AgentVO agentVO) {
        if (agentVO.getModel() != null) {
            // 根据配置选择模型
            ChatModel model = resolveModel(agentVO.getModel());
            builder.model(model);
        }
    }
}

// Prompt 注入器
public class NacosPromptInjector implements NacosAgentInjector {
    @Override
    public void inject(ReactAgent.Builder builder, AgentVO agentVO) {
        if (agentVO.getPrompt() != null) {
            builder.instruction(agentVO.getPrompt().getSystemPrompt());
        }
    }
}

// MCP 工具注入器
public class NacosMcpToolsInjector implements NacosAgentInjector {
    @Override
    public void inject(ReactAgent.Builder builder, AgentVO agentVO) {
        if (agentVO.getMcpServers() != null) {
            List<ToolCallback> tools = loadMcpTools(agentVO.getMcpServers());
            builder.toolCallbacks(tools);
        }
    }
}
```

---

## 6. 设计总结

### 6.1 关键设计原则

1. **自动配置优先**: 所有 Starter 都基于 Spring Boot Auto-Configuration
2. **条件装配**: 使用 `@ConditionalOnXxx` 实现按需加载
3. **可扩展性**: 核心接口可替换，支持自定义实现
4. **可观测性**: 内置 Micrometer 集成，支持分布式追踪

### 6.2 模块依赖关系

```
spring-ai-alibaba-starter-a2a-nacos
    ├── spring-ai-alibaba-graph-core (Agent 抽象)
    ├── nacos-api (Nacos SDK)
    └── a2a-spec (A2A 协议规范)

spring-ai-alibaba-starter-builtin-nodes
    ├── spring-ai-alibaba-graph-core (State, NodeAction)
    └── spring-ai-core (ChatClient, ToolCallback)

spring-ai-alibaba-starter-config-nacos
    ├── spring-ai-alibaba-agent-framework
    ├── nacos-api
    └── spring-ai-core

spring-ai-alibaba-starter-graph-observation
    ├── spring-ai-alibaba-graph-core
    └── micrometer-observation
```
