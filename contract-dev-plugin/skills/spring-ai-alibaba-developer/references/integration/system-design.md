# Spring AI Alibaba Integration 系统设计

## 1. Agent 注册与发现系统

### 1.1 系统架构

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           应用层                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐│
│  │  Service A (Agent Provider)                                         ││
│  │  ┌─────────────────┐    ┌──────────────────────────────────────┐   ││
│  │  │ ReactAgent      │───▶│ A2aServerAutoConfiguration           │   ││
│  │  │ (data_analysis) │    │ - 暴露 /.well-known/agent.json       │   ││
│  │  └─────────────────┘    │ - 暴露 /message 端点                 │   ││
│  │                         │ - 注册 AgentCard 到 Nacos             │   ││
│  │                         └──────────────────────────────────────┘   ││
│  └─────────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼ 注册
┌─────────────────────────────────────────────────────────────────────────┐
│                        Nacos 注册中心                                    │
│  ┌─────────────────────────────────────────────────────────────────────┐│
│  │  A2A 服务注册表                                                      ││
│  │  ┌───────────────────────────────────────────────────────────────┐  ││
│  │  │  data_analysis_agent                                           │  ││
│  │  │  - url: http://192.168.1.100:8080                             │  ││
│  │  │  - capabilities: [data-analysis, statistics]                  │  ││
│  │  │  - skills: [trend-analysis, report-generation]                │  ││
│  │  └───────────────────────────────────────────────────────────────┘  ││
│  │  ┌───────────────────────────────────────────────────────────────┐  ││
│  │  │  code_review_agent                                             │  ││
│  │  │  - url: http://192.168.1.101:8080                             │  ││
│  │  │  - capabilities: [code-analysis, review]                      │  ││
│  │  └───────────────────────────────────────────────────────────────┘  ││
│  └─────────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼ 发现
┌─────────────────────────────────────────────────────────────────────────┐
│                           应用层                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐│
│  │  Service B (Agent Consumer)                                         ││
│  │  ┌─────────────────────────────────────────────────────────────┐   ││
│  │  │ A2aRemoteAgent.builder()                                      │   ││
│  │  │     .name("data_analysis_agent")                              │   ││
│  │  │     .agentCardProvider(nacosAgentCardProvider)               │   ││
│  │  │     .build()                                                  │   ││
│  │  └─────────────────────────────────────────────────────────────┘   ││
│  └─────────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────────┘
```

### 1.2 注册流程详解

```java
// 1. 定义 Agent Bean
@Configuration
public class AgentConfig {
    
    @Bean
    public ReactAgent dataAnalysisAgent(ChatModel chatModel) {
        return ReactAgent.builder()
            .name("data_analysis_agent")
            .model(chatModel)
            .description("数据分析智能体")
            .instruction("你是一个数据分析专家...")
            .build();
    }
    
    // 2. 实现 AgentLoader（可选，用于动态加载）
    @Bean
    public AgentLoader agentLoader(ReactAgent dataAnalysisAgent) {
        return new AgentLoader() {
            @Override
            public List<String> listAgents() {
                return List.of(dataAnalysisAgent.name());
            }
            
            @Override
            public Agent loadAgent(String name) {
                if (dataAnalysisAgent.name().equals(name)) {
                    return dataAnalysisAgent;
                }
                throw new NoSuchElementException("Agent not found: " + name);
            }
        };
    }
}
```

**自动注册机制：**

1. `A2aServerAgentCardAutoConfiguration` 自动创建 AgentCard
2. `A2aServerRegistryAutoConfiguration` 注册本地 Agent
3. `NacosA2aRegistryAutoConfiguration` 将 Agent 注册到 Nacos

### 1.3 发现流程详解

```java
// 消费端配置
@Configuration
public class ConsumerConfig {
    
    @Bean
    public A2aRemoteAgent dataAnalysisRemoteAgent(
            AgentCardProvider agentCardProvider) {
        return A2aRemoteAgent.builder()
            .name("data_analysis_agent")
            .agentCardProvider(agentCardProvider)  // 从 Nacos 获取 AgentCard
            .description("远程数据分析代理")
            .instruction("{input}")
            .build();
    }
}
```

**发现机制：**

1. `NacosA2aDiscoveryAutoConfiguration` 配置 `NacosAgentCardProvider`
2. `AgentCardProvider.getAgentCard(name)` 从 Nacos 查询
3. `A2aRemoteAgent` 使用 AgentCard 建立远程连接

---

## 2. 跨 Agent 通信流程

### 2.1 JSON-RPC 通信协议

```
┌─────────────────┐                              ┌─────────────────┐
│   Client        │                              │   Server        │
│ (A2aRemoteAgent)│                              │ (ReactAgent)    │
└────────┬────────┘                              └────────┬────────┘
         │                                                │
         │  POST /message                                 │
         │  Content-Type: application/json               │
         │  {                                             │
         │    "jsonrpc": "2.0",                          │
         │    "method": "send_message",                  │
         │    "params": {                                │
         │      "message": {                             │
         │        "role": "user",                        │
         │        "content": "分析销售数据"              │
         │      }                                        │
         │    },                                         │
         │    "id": "req-001"                            │
         │  }                                            │
         │───────────────────────────────────────────────▶│
         │                                                │
         │                                                │ 执行 Agent
         │                                                │ invoke(input)
         │                                                │
         │  {                                             │
         │    "jsonrpc": "2.0",                          │
         │    "result": {                                │
         │      "status": "completed",                   │
         │      "output": "分析结果..."                   │
         │    },                                         │
         │    "id": "req-001"                            │
         │  }                                            │
         │◀───────────────────────────────────────────────│
         │                                                │
```

### 2.2 流式通信

```
┌─────────────────┐                              ┌─────────────────┐
│   Client        │                              │   Server        │
└────────┬────────┘                              └────────┬────────┘
         │                                                │
         │  POST /message (streaming)                     │
         │  Accept: text/event-stream                    │
         │───────────────────────────────────────────────▶│
         │                                                │
         │  data: {"event": "task_started", ...}         │
         │◀───────────────────────────────────────────────│
         │                                                │
         │  data: {"event": "content_block_delta",       │
         │         "delta": {"text": "正在"}}            │
         │◀───────────────────────────────────────────────│
         │                                                │
         │  data: {"event": "content_block_delta",       │
         │         "delta": {"text": "分析"}}            │
         │◀───────────────────────────────────────────────│
         │                                                │
         │  data: {"event": "task_completed", ...}       │
         │◀───────────────────────────────────────────────│
         │                                                │
```

### 2.3 请求处理器设计

```java
public class JsonRpcA2aRequestHandler implements A2aRequestHandler {

    @Override
    public Flux<JSONRPCResponse> handleRequest(JSONRPCRequest request) {
        // 解析请求类型
        if (request instanceof SendStreamingMessageRequest streamingRequest) {
            return handleStreamingMessage(streamingRequest);
        } else if (request instanceof SendMessageRequest messageRequest) {
            return handleMessage(messageRequest).flux();
        }
        // ...
    }
    
    private Flux<JSONRPCResponse> handleStreamingMessage(
            SendStreamingMessageRequest request) {
        return Flux.create(emitter -> {
            // 注入流式元数据
            OverAllState state = buildState(request);
            state.withStreamingMetadata(true);
            
            // 执行 Agent
            graphAgentExecutor.execute(state)
                .subscribe(response -> {
                    emitter.next(convertToResponse(response));
                }, emitter::error, emitter::complete);
        });
    }
}
```

---

## 3. 配置热更新机制

### 3.1 Nacos 配置监听

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        Nacos Config Server                               │
│  ┌─────────────────────────────────────────────────────────────────────┐│
│  │  Data ID: agent-config.yaml                                         ││
│  │  Group: DEFAULT_GROUP                                               ││
│  │                                                                     ││
│  │  agent:                                                             ││
│  │    name: data_analysis_agent                                        ││
│  │    model:                                                           ││
│  │      provider: dashscope                                            ││
│  │      name: qwen-plus                                                ││
│  │    prompt:                                                          ││
│  │      system: "你是一个数据分析专家..."                               ││
│  │    mcp-servers:                                                     ││
│  │      - name: database-tools                                         ││
│  │        url: http://mcp-server:8080                                  ││
│  └─────────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ 配置变更通知
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        Spring Application                                │
│  ┌─────────────────────────────────────────────────────────────────────┐│
│  │  NacosAgentConfig                                                   ││
│  │  ┌─────────────────────────────────────────────────────────────┐   ││
│  │  │  @NacosConfigListener(dataId = "agent-config.yaml")         │   ││
│  │  │  public void onConfigChange(String newConfig) {             │   ││
│  │  │      // 解析新配置                                          │   ││
│  │  │      AgentVO agentVO = parseConfig(newConfig);              │   ││
│  │  │      // 重新构建 Agent                                       │   ││
│  │  │      rebuildAgent(agentVO);                                 │   ││
│  │  │  }                                                          │   ││
│  │  └─────────────────────────────────────────────────────────────┘   ││
│  └─────────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────────┘
```

### 3.2 配置注入流程

```java
// 1. 加载配置
Properties props = nacosAgentProxyProperties;
String agentName = props.getProperty("agentName");
String promptKey = props.getProperty("promptKey");

// 2. 构建选项
NacosOptions nacosOptions = new NacosOptions(props);

// 3. 注入组件
List<NacosAgentInjector> injectors = List.of(
    new NacosModelInjector(),
    new NacosPromptInjector(),
    new NacosMcpToolsInjector(),
    new NacosPartnerAgentsInjector()
);

// 4. 构建 Agent
ReactAgent.Builder builder = ReactAgent.builder()
    .name(agentName);

for (NacosAgentInjector injector : injectors) {
    injector.inject(builder, agentVO);
}

ReactAgent agent = builder.build();
```

### 3.3 动态配置示例

```yaml
# Nacos: agent-config.yaml
agent:
  name: data_analysis_agent
  description: 数据分析智能体
  
  model:
    provider: dashscope
    name: qwen-plus
    options:
      temperature: 0.7
      max-tokens: 4096
      
  prompt:
    system: |
      你是一个专业的数据分析专家。
      你的职责是：
      1. 分析用户提供的业务数据
      2. 识别数据中的趋势和模式
      3. 提供可操作的建议
      
  memory:
    type: conversational
    max-messages: 20
    
  mcp-servers:
    - name: database-tools
      url: ${DATABASE_MCP_URL}
      tools:
        - query_database
        - export_report
        
  partner-agents:
    - name: visualization_agent
      description: 数据可视化专家
```

---

## 4. 可观测性系统集成

### 4.1 分布式追踪

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         Trace Context                                    │
│  trace-id: abc123-def456-ghi789                                         │
│  span-id: span-001                                                      │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
         ┌──────────────────────────┼──────────────────────────┐
         ▼                          ▼                          ▼
┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐
│    Span 1       │      │    Span 2       │      │    Span 3       │
│  A2aRemoteAgent │─────▶│  JsonRpcHandler │─────▶│  GraphAgentExec │
│  invoke()       │      │  handleRequest()│      │  execute()      │
│  duration: 2.5s │      │  duration: 2.4s │      │  duration: 2.3s │
└─────────────────┘      └─────────────────┘      └─────────────────┘
                                                            │
                                     ┌──────────────────────┼──────────────────────┐
                                     ▼                      ▼                      ▼
                           ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
                           │    Span 4       │    │    Span 5       │    │    Span 6       │
                           │  LlmNode        │    │  ToolNode       │    │  AnswerNode     │
                           │  apply()        │    │  apply()        │    │  apply()        │
                           │  duration: 1.8s │    │  duration: 0.3s │    │  duration: 0.1s │
                           └─────────────────┘    └─────────────────┘    └─────────────────┘
```

### 4.2 指标采集

```java
// GraphObservationHandler 采集的指标
public class GraphObservationHandler {
    
    // Graph 级别指标
    meterRegistry.counter("graph.execution.count",
        "graph.name", graphName,
        "status", status
    ).increment();
    
    meterRegistry.timer("graph.execution.duration",
        "graph.name", graphName
    ).record(duration);
    
    // Node 级别指标
    meterRegistry.counter("node.execution.count",
        "node.name", nodeName,
        "node.type", nodeType
    ).increment();
    
    // Token 使用指标
    meterRegistry.counter("llm.tokens.used",
        "model", modelName,
        "type", "input"
    ).increment(inputTokens);
}
```

### 4.3 日志关联

```java
// 使用 MDC 关联日志
public class GraphObservationLifecycleListener {
    
    @Override
    public void onGraphStart(GraphExecutionContext context) {
        MDC.put("traceId", context.getTraceId());
        MDC.put("graphName", context.getGraphName());
        log.info("Graph execution started");
    }
    
    @Override
    public void onGraphEnd(GraphExecutionContext context) {
        log.info("Graph execution completed in {} ms", 
            context.getDuration().toMillis());
        MDC.clear();
    }
}
```

---

## 5. 系统集成最佳实践

### 5.1 高可用部署

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           Load Balancer                                  │
└─────────────────────────────────────────────────────────────────────────┘
         │                          │                          │
         ▼                          ▼                          ▼
┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐
│  Agent Server 1 │      │  Agent Server 2 │      │  Agent Server 3 │
│  (data_analysis)│      │  (data_analysis)│      │  (data_analysis)│
└────────┬────────┘      └────────┬────────┘      └────────┬────────┘
         │                        │                        │
         └────────────────────────┼────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                     Nacos Cluster (HA)                                   │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐                  │
│  │  Nacos 1    │◀──▶│  Nacos 2    │◀──▶│  Nacos 3    │                  │
│  │  (Leader)   │    │  (Follower) │    │  (Follower) │                  │
│  └─────────────┘    └─────────────┘    └─────────────┘                  │
└─────────────────────────────────────────────────────────────────────────┘
```

### 5.2 容错策略

```java
// 重试配置
@Configuration
public class ResilienceConfig {
    
    @Bean
    public RetryConfig a2aRetryConfig() {
        return RetryConfig.custom()
            .maxAttempts(3)
            .waitDuration(Duration.ofMillis(500))
            .retryOnException(e -> e instanceof A2aConnectionException)
            .build();
    }
    
    @Bean
    public CircuitBreakerConfig a2aCircuitBreakerConfig() {
        return CircuitBreakerConfig.custom()
            .failureRateThreshold(50)
            .waitDurationInOpenState(Duration.ofSeconds(30))
            .slidingWindowSize(10)
            .build();
    }
}
```

### 5.3 安全配置

```yaml
# application.yml
spring:
  ai:
    alibaba:
      a2a:
        server:
          card:
            security-schemes:
              bearer:
                type: http
                scheme: bearer
                bearer-format: JWT
            security:
              - bearer: []
```
