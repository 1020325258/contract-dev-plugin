# Spring AI Alibaba Studio & Admin 核心设计分析

## 1. Studio 嵌入式 UI 设计

### 1.1 设计理念

Studio 采用"嵌入式 UI"设计理念，将 Agent 调试界面直接集成到 Spring Boot 应用中，开发者无需额外部署前端服务即可进行 Agent 调试。

### 1.2 双模式部署

#### 嵌入模式（Embedded Mode）
- 前端静态资源打包到 Spring Boot JAR 中
- 访问路径：`http://localhost:{port}/chatui/index.html`
- 适用场景：开发调试、单机部署

```xml
<dependency>
    <groupId>com.alibaba.cloud.ai</groupId>
    <artifactId>spring-ai-alibaba-studio</artifactId>
    <version>1.1.2.0</version>
</dependency>
```

#### 独立模式（Standalone Mode）
- 前端独立运行 Next.js 开发服务器
- 后端服务独立部署
- 适用场景：团队协作、前后端分离开发

```bash
# 前端
pnpm dev  # http://localhost:3000

# 后端
mvn spring-boot:run  # http://localhost:8080
```

### 1.3 前后端通信机制

#### SSE（Server-Sent Events）流式通信

Studio 采用 SSE 实现前后端实时通信，支持流式响应：

```
客户端                          服务端
   |                              |
   |--- POST /run_sse ----------->|
   |                              |
   |<-- SSE: event stream --------|
   |<-- data: {"chunk": "..."} ---|
   |<-- data: {"chunk": "..."} ---|
   |<-- data: {"message": {...}} -|
   |                              |
```

#### API 客户端设计

```typescript
// src/lib/spring-ai-api.ts
class SpringAIApiClient {
  // SSE 流式运行
  async runAgentStream(request: AgentRunRequest): Promise<ReadableStream> {
    const response = await fetch(`${apiUrl}/run_sse`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'text/event-stream',
      },
      body: JSON.stringify(request),
    });
    return response.body;
  }

  // HitL 恢复执行
  async resumeAgentStream(request: AgentResumeRequest): Promise<ReadableStream> {
    // ...
  }
}
```

### 1.4 Agent 加载机制

#### AgentLoader 接口

```java
public interface AgentLoader {
    /**
     * 返回可用 Agent 名称列表
     */
    @Nonnull
    List<String> listAgents();

    /**
     * 根据名称加载 Agent 实例
     */
    Agent loadAgent(String name);
}
```

#### 自定义 Agent 加载示例

```java
@Component
public class MyAgentLoader implements AgentLoader {
    @Override
    public List<String> listAgents() {
        return List.of("chat_bot", "code_assistant");
    }

    @Override
    public Agent loadAgent(String name) {
        switch (name) {
            case "chat_bot":
                return createChatBot();
            case "code_assistant":
                return createCodeAssistant();
            default:
                throw new NoSuchElementException("Agent not found: " + name);
        }
    }
}
```

---

## 2. Admin 平台架构

### 2.1 模块化架构设计

Admin 采用多模块架构，职责清晰分离：

```
spring-ai-alibaba-admin
├── admin-server-start    # 启动入口、REST 控制器
├── admin-server-core     # 核心业务逻辑
├── admin-server-openapi  # OpenAPI 接口层
└── admin-server-runtime  # 运行时支持
```

### 2.2 核心功能模块

#### Prompt 管理
- **模板管理**: 创建、更新、删除 Prompt 模板
- **版本控制**: 版本管理、历史追踪
- **实时调试**: 在线调试、流式响应
- **会话管理**: 多轮对话支持

#### 数据集管理
- **数据集创建**: 多格式导入
- **版本管理**: 数据集版本控制
- **从 Trace 创建**: 支持 OpenTelemetry Trace 数据转换

#### 评估器管理
- **评估器配置**: 创建和配置评估器
- **模板系统**: 评估器模板、自定义逻辑
- **版本管理**: 版本控制、发布管理

#### 实验管理
- **实验执行**: 自动化评估实验
- **结果分析**: 详细统计与分析
- **批量处理**: 批量执行、结果对比

### 2.3 多租户设计

Admin 通过 Workspace（工作空间）实现多租户隔离：

```java
@Service
public class WorkspaceServiceImpl implements WorkspaceService {
    // 工作空间隔离
    // 用户权限管理
    // 资源配额控制
}
```

---

## 3. 可视化调试设计思想

### 3.1 状态管理架构

Studio 采用 React Context + Provider 模式进行状态管理：

```
RootLayout
└── ThreadProvider          # 会话 CRUD 状态
    └── StreamProvider      # 消息流处理
        └── ArtifactProvider # 侧边面板上下文
            └── Thread      # 主聊天界面
```

#### ThreadProvider - 会话状态

```typescript
interface ThreadState {
  threads: Thread[];
  currentThreadId: string | null;
  isLoading: boolean;
}

// 会话 CRUD
const { threads, createThread, deleteThread, selectThread } = useThreads();
```

#### StreamProvider - 消息流状态

```typescript
interface StreamState {
  messages: Message[];
  isStreaming: boolean;
}

// 消息发送与恢复
const { messages, sendMessage, resumeFeedback } = useStream();
```

### 3.2 消息类型系统

| messageType | 组件 | 说明 |
|-------------|------|------|
| `'user'` | HumanMessage | 用户消息，右对齐气泡 |
| `'assistant'` | AssistantMessage | AI 回复，Markdown 渲染 |
| `'tool-request'` | ToolRequestMessage | 工具调用展示 |
| `'tool-confirm'` | ToolRequestConfirmMessage | HitL 审批面板 |
| `'tool'` | ToolResponseMessage | 工具结果展示 |

### 3.3 人机协作（HitL）流程

```
用户提交消息
    ↓
Agent 执行
    ↓
需要人工审批的工具调用?
    ├─ 是 → 返回 tool-confirm 消息
    │        ↓
    │      用户审批（批准/拒绝）
    │        ↓
    │      POST /resume_sse
    │        ↓
    │      继续执行
    │
    └─ 否 → 直接返回结果
```

#### 代码实现

```typescript
// StreamProvider.tsx
const resumeFeedback = async (feedback: ToolFeedback) => {
  const request: AgentResumeRequest = {
    appName,
    threadId,
    userId,
    toolFeedbacks: [feedback],
  };

  const stream = await apiClient.resumeAgentStream(request);
  processStream(stream);
};
```

---

## 4. 日志与追踪集成

### 4.1 OpenTelemetry 集成

Admin 集成 OpenTelemetry 提供完整的 Trace 追踪：

```yaml
# Agent 应用配置
management:
  otlp:
    tracing:
      export:
        enabled: true
      endpoint: http://{admin-address}:4318/v1/traces
  tracing:
    sampling:
      probability: 1.0
  opentelemetry:
    resource-attributes:
      service:
        name: my-agent-app
        version: 1.0
```

### 4.2 Micrometer 集成

```yaml
spring:
  ai:
    chat:
      client:
        observations:
          log-prompt: true
    chat:
      observations:
        log-prompt: true
        log-completion: true
```

### 4.3 Trace 数据流

```
Agent 应用
    ↓
OTel SDK (Span 生成)
    ↓
OTLP Exporter
    ↓
Admin (OTel Collector)
    ↓
存储 & 可视化
```

---

## 5. Nacos 集成设计

### 5.1 Prompt 动态加载

Admin 通过 Nacos 实现 Prompt 动态加载与更新：

```yaml
# Agent 应用配置
spring:
  ai:
    alibaba:
      agent:
        proxy:
          nacos:
            serverAddr: 127.0.0.1:8848
            username: nacos
            password: nacos
            promptKey: my-agent-prompt
```

### 5.2 配置同步流程

```
Admin 平台
    ↓ (更新 Prompt)
Nacos Config Server
    ↓ (配置推送)
Agent 应用
    ↓ (热加载)
新的 Prompt 生效
```

---

## 6. 模型配置管理

### 6.1 多模型支持

Admin 支持多种 AI 模型提供商：

| 提供商 | 配置文件 |
|--------|----------|
| DashScope | model-config-dashscope.yaml |
| DeepSeek | model-config-deepseek.yaml |
| OpenAI | model-config-openai.yaml |

### 6.2 动态配置

```yaml
# model-config.yaml
spring:
  ai:
    dashscope:
      api-key: ${DASHSCOPE_API_KEY}
      chat:
        options:
          model: qwen-max
```

### 6.3 运行时更新

Admin 支持运行时动态更新模型配置，无需重启服务。
