# Spring AI Alibaba Integration 配置参考

## 1. A2A Nacos 配置

### 1.1 Server 配置

```yaml
spring:
  ai:
    alibaba:
      a2a:
        server:
          # 传输类型 (json-rpc / grpc)
          type: json-rpc
          # AgentCard 端点 URL
          agent-card-url: /.well-known/agent.json
          # 消息处理端点 URL
          message-url: /message
          # 服务地址 (自动检测)
          address: ${server.address:}
          # 服务端口 (自动检测)
          port: ${server.port:}
          # Agent 版本
          version: 1.0.0
```

### 1.2 AgentCard 配置

```yaml
spring:
  ai:
    alibaba:
      a2a:
        server:
          card:
            # Agent 名称
            name: my_agent
            # Agent 描述
            description: 我的智能体服务
            # 文档 URL
            documentation-url: https://docs.example.com
            # 图标 URL
            icon-url: https://example.com/icon.png
            # 提供者信息
            provider:
              name: My Organization
              organization: My Company
              url: https://my-company.com
              contact:
                email: support@my-company.com
            # 能力定义
            capabilities:
              streaming: true
              push-notifications: false
            # 输入输出模式
            default-input-modes:
              - text
            default-output-modes:
              - text
            # 技能列表
            skills:
              - id: data-analysis
                name: 数据分析
                description: 分析业务数据
                tags:
                  - analysis
                  - statistics
```

### 1.3 Nacos 连接配置

```yaml
spring:
  ai:
    alibaba:
      a2a:
        nacos:
          # Nacos 服务地址
          server-addr: 127.0.0.1:8848
          # 命名空间
          namespace: public
          # 用户名
          username: nacos
          # 密码
          password: nacos
          # Access Key (阿里云)
          access-key: ${NACOS_ACCESS_KEY:}
          # Secret Key (阿里云)
          secret-key: ${NACOS_SECRET_KEY:}
          # Endpoint (阿里云)
          endpoint: ${NACOS_ENDPOINT:}
```

### 1.4 Registry 配置

```yaml
spring:
  ai:
    alibaba:
      a2a:
        nacos:
          registry:
            # 是否启用注册
            enabled: true
            # 注册分组
            group-name: DEFAULT_GROUP
            # 服务名称
            service-name: ${spring.application.name}
```

### 1.5 Discovery 配置

```yaml
spring:
  ai:
    alibaba:
      a2a:
        nacos:
          discovery:
            # 是否启用发现
            enabled: true
            # 发现分组
            group-name: DEFAULT_GROUP
```

---

## 2. Config Nacos 配置

### 2.1 基础配置

```yaml
spring:
  ai:
    alibaba:
      agent:
        proxy:
          nacos:
            # 是否启用
            enabled: true
            # Nacos 服务地址
            server-addr: 127.0.0.1:8848
            # 命名空间
            namespace: public
            # 分组
            group: DEFAULT_GROUP
            # Data ID
            data-id: agent-config.yaml
            # Agent 名称
            agent-name: dynamic_agent
            # Prompt Key
            prompt-key: agent_prompt
```

### 2.2 Agent 配置结构 (Nacos Data ID)

```yaml
agent:
  # Agent 基本信息
  name: data_analysis_agent
  description: 数据分析智能体
  
  # 模型配置
  model:
    provider: dashscope
    name: qwen-plus
    options:
      temperature: 0.7
      max-tokens: 4096
      top-p: 0.9
      
  # Prompt 配置
  prompt:
    system: |
      你是一个专业的数据分析专家。
      你的职责是分析数据并提供见解。
      
  # 记忆配置
  memory:
    type: conversational
    max-messages: 20
    
  # MCP 服务器配置
  mcp-servers:
    - name: database-tools
      url: http://mcp-server:8080
      tools:
        - query_database
        - export_report
        
  # 合作 Agent 配置
  partner-agents:
    - name: visualization_agent
      description: 数据可视化专家
      url: http://viz-agent:8080
```

---

## 3. Graph Observation 配置

### 3.1 基础配置

```yaml
spring:
  ai:
    alibaba:
      graph:
        observation:
          # 是否启用观测
          enabled: true
```

### 3.2 Management 配置

```yaml
management:
  # 观测配置
  observations:
    enabled: true
    
  # 追踪配置
  tracing:
    enabled: true
    sampling:
      probability: 1.0
      
  # 端点配置
  endpoints:
    web:
      exposure:
        include: prometheus, health, info, metrics, tracing
        
  # Prometheus 配置
  prometheus:
    metrics:
      export:
        enabled: true
```

### 3.3 OpenTelemetry 配置

```yaml
otel:
  # 导出器配置
  exporter:
    otlp:
      endpoint: http://localhost:4317
      
  # 追踪配置
  traces:
    exporter: otlp
    
  # 指标配置
  metrics:
    exporter: otlp
    
  # 日志配置
  logs:
    exporter: otlp
```

---

## 4. MCP 配置

### 4.1 SSE 连接配置

```yaml
spring:
  ai:
    mcp:
      client:
        enabled: true
        name: saa-mcp-client
        type: async
        toolcallback:
          enabled: true
        sse:
          connections:
            mcp-server-1:
              url: http://mcp-server:8080
              sse-endpoint: sse
```

### 4.2 Streamable HTTP 配置

```yaml
spring:
  ai:
    mcp:
      client:
        enabled: true
        streamable-http:
          connections:
            amap-maps:
              url: ${MODEL_SCOPE_AMAP_BASE_URL}
              endpoint: mcp
```

---

## 5. 环境变量参考

### 5.1 A2A 相关

| 环境变量 | 说明 | 默认值 |
|---------|------|--------|
| `NACOS_SERVER_ADDR` | Nacos 服务地址 | 127.0.0.1:8848 |
| `NACOS_USERNAME` | Nacos 用户名 | nacos |
| `NACOS_PASSWORD` | Nacos 密码 | nacos |
| `NACOS_NAMESPACE` | 命名空间 | public |
| `NACOS_ACCESS_KEY` | Access Key | - |
| `NACOS_SECRET_KEY` | Secret Key | - |

### 5.2 模型相关

| 环境变量 | 说明 |
|---------|------|
| `DASHSCOPE_API_KEY` | 阿里云百炼 API Key |
| `DASHSCOPE_MODEL` | 模型名称 |

### 5.3 MCP 相关

| 环境变量 | 说明 |
|---------|------|
| `MODEL_SCOPE_AMAP_BASE_URL` | 高德地图 MCP URL |
| `MODEL_SCOPE_12306_BASE_URL` | 12306 MCP URL |

---

## 6. 完整配置示例

```yaml
server:
  port: 8080
  
spring:
  application:
    name: agent-service
    
  ai:
    # DashScope 配置
    dashscope:
      api-key: ${DASHSCOPE_API_KEY}
      chat:
        options:
          model: qwen-plus
          
    # A2A Nacos 配置
    alibaba:
      a2a:
        nacos:
          server-addr: ${NACOS_SERVER_ADDR:127.0.0.1:8848}
          username: ${NACOS_USERNAME:nacos}
          password: ${NACOS_PASSWORD:nacos}
          discovery:
            enabled: true
          registry:
            enabled: true
        server:
          version: 1.0.0
          card:
            name: my_agent
            description: 我的智能体服务
            provider:
              name: My Organization
              
      # Config Nacos 配置
      agent:
        proxy:
          nacos:
            enabled: true
            agent-name: dynamic_agent
            
      # Graph Observation 配置
      graph:
        observation:
          enabled: true
          
    # MCP 配置
    mcp:
      client:
        enabled: true
        name: saa-mcp-client
        type: async
        toolcallback:
          enabled: true
          
# Management 配置
management:
  observations:
    enabled: true
  tracing:
    enabled: true
  endpoints:
    web:
      exposure:
        include: prometheus, health, info
        
# 日志配置
logging:
  level:
    root: INFO
    com.alibaba.cloud.ai: DEBUG
