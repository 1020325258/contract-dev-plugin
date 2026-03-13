# Spring AI Alibaba Studio & Admin 系统设计

## 1. Studio 与 Agent 的通信机制

### 1.1 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                        Browser                               │
│  ┌──────────────────────────────────────────────────────┐   │
│  │                  Next.js App                          │   │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐     │   │
│  │  │ThreadProvider│ │StreamProvider│ │ArtifactProvider│   │   │
│  │  └────────────┘  └────────────┘  └────────────┘     │   │
│  │         │               │               │             │   │
│  │         └───────────────┼───────────────┘             │   │
│  │                         ▼                             │   │
│  │              ┌─────────────────────┐                  │   │
│  │              │ SpringAIApiClient   │                  │   │
│  │              └─────────────────────┘                  │   │
│  └─────────────────────────│─────────────────────────────┘   │
└────────────────────────────│────────────────────────────────┘
                             │ HTTP/SSE
                             ▼
┌─────────────────────────────────────────────────────────────┐
│                    Spring Boot Application                   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │                  Studio Module                        │   │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐     │   │
│  │  │AgentController│ │ThreadController│ │ExecutionController│  │
│  │  └────────────┘  └────────────┘  └────────────┘     │   │
│  │         │               │               │             │   │
│  │         └───────────────┼───────────────┘             │   │
│  │                         ▼                             │   │
│  │              ┌─────────────────────┐                  │   │
│  │              │   AgentLoader       │                  │   │
│  │              └─────────────────────┘                  │   │
│  └─────────────────────────│─────────────────────────────┘   │
│                            ▼                                 │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              Agent Framework                          │   │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐     │   │
│  │  │    Agent    │ │  Graph Core │ │    Tools    │     │   │
│  │  └────────────┘  └────────────┘  └────────────┘     │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 SSE 流式通信详解

#### 请求流程

```
1. 用户输入消息
2. StreamProvider.sendMessage()
3. POST /run_sse (Accept: text/event-stream)
4. ExecutionController.agentRunSse()
5. Agent.stream() → Flux<NodeOutput>
6. SSE 事件流返回前端
7. StreamProvider 处理事件更新 UI
```

#### SSE 事件格式

```json
// 流式 chunk
data: {"node":"agent","agent":"chat_bot","chunk":"Hello"}

// 完整消息
data: {"node":"agent","agent":"chat_bot","message":{"type":"assistant","content":"..."},"tokenUsage":{...}}

// 工具确认请求
data: {"node":"agent","message":{"messageType":"tool-confirm","toolCalls":[...]}}
```

### 1.3 HitL（人机协作）通信流程

```
┌──────────┐      ┌──────────┐      ┌──────────┐
│  Client  │      │  Server  │      │  Agent   │
└────┬─────┘      └────┬─────┘      └────┬─────┘
     │                 │                 │
     │ POST /run_sse   │                 │
     │────────────────>│                 │
     │                 │ stream()        │
     │                 │────────────────>│
     │                 │                 │
     │ SSE: tool-confirm                 │
     │<────────────────│<────────────────│
     │                 │                 │
     │ [用户审批]       │                 │
     │                 │                 │
     │ POST /resume_sse│                 │
     │────────────────>│                 │
     │                 │ stream(feedback)│
     │                 │────────────────>│
     │                 │                 │
     │ SSE: 最终结果    │                 │
     │<────────────────│<────────────────│
     │                 │                 │
```

---

## 2. Admin 多租户设计

### 2.1 多租户架构

```
┌─────────────────────────────────────────────────────────────┐
│                     Admin Platform                           │
│  ┌─────────────────────────────────────────────────────┐    │
│  │                   Workspace Layer                    │    │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐          │    │
│  │  │Workspace1│  │Workspace2│  │Workspace3│           │    │
│  │  │ Tenant A │  │ Tenant B │  │ Tenant C │           │    │
│  │  └──────────┘  └──────────┘  └──────────┘          │    │
│  └─────────────────────────────────────────────────────┘    │
│                            │                                 │
│                            ▼                                 │
│  ┌─────────────────────────────────────────────────────┐    │
│  │                   Service Layer                      │    │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐          │    │
│  │  │PromptSvc │  │DatasetSvc│  │ExperimentSvc│        │    │
│  │  └──────────┘  └──────────┘  └──────────┘          │    │
│  └─────────────────────────────────────────────────────┘    │
│                            │                                 │
│                            ▼                                 │
│  ┌─────────────────────────────────────────────────────┐    │
│  │                   Data Layer                         │    │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐          │    │
│  │  │  MySQL   │  │Elasticsearch│ │  Redis  │          │    │
│  │  └──────────┘  └──────────┘  └──────────┘          │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 隔离机制

#### 数据隔离
- 每个工作空间独立的数据库 Schema 或租户 ID
- 查询自动注入租户条件

#### 权限隔离
- 工作空间级别的角色权限
- API Key 与工作空间绑定

#### 资源隔离
- 资源配额限制
- 并发执行数限制

### 2.3 Workspace 服务

```java
@Service
public class WorkspaceServiceImpl implements WorkspaceService {

    /**
     * 获取当前用户的默认工作空间
     */
    public Workspace getDefaultWorkspace(String userId);

    /**
     * 创建新工作空间
     */
    public Workspace createWorkspace(WorkspaceCreateRequest request);

    /**
     * 工作空间成员管理
     */
    public void addMember(String workspaceId, String userId, Role role);
}
```

---

## 3. 日志与追踪集成

### 3.1 可观测性架构

```
┌─────────────────────────────────────────────────────────────┐
│                     Agent Applications                       │
│  ┌─────────────────────────────────────────────────────┐    │
│  │                  OTel SDK                            │    │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐          │    │
│  │  │  Tracer  │  │ MeterProvider│ │LoggerProvider│    │    │
│  │  └──────────┘  └──────────┘  └──────────┘          │    │
│  └─────────────────────────────────────────────────────┘    │
│                            │                                 │
│                            ▼ OTLP Protocol                   │
│  ┌─────────────────────────────────────────────────────┐    │
│  │               Admin OTel Collector                   │    │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐          │    │
│  │  │ Receiver │  │ Processor │  │ Exporter │          │    │
│  │  └──────────┘  └──────────┘  └──────────┘          │    │
│  └─────────────────────────────────────────────────────┘    │
│                            │                                 │
│                            ▼                                 │
│  ┌─────────────────────────────────────────────────────┐    │
│  │                  Storage Layer                       │    │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐          │    │
│  │  │  Trace   │  │  Metrics │  │  Logs    │          │    │
│  │  │ Storage  │  │ Storage  │  │ Storage  │          │    │
│  │  └──────────┘  └──────────┘  └──────────┘          │    │
│  └─────────────────────────────────────────────────────┘    │
│                            │                                 │
│                            ▼                                 │
│  ┌─────────────────────────────────────────────────────┐    │
│  │                 Admin UI Dashboard                   │    │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐          │    │
│  │  │Trace View│  │Metrics View│ │Logs View│           │    │
│  │  └──────────┘  └──────────┘  └──────────┘          │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

### 3.2 Trace 数据模型

```
Trace
├── Span: ChatClient.call()
│   ├── Span: Model.chat()
│   │   └── Span: API Request
│   ├── Span: Tool Execution
│   │   └── Span: Tool Handler
│   └── Span: Response Processing
```

### 3.3 配置示例

```yaml
# Agent 应用 OTel 配置
management:
  otlp:
    tracing:
      export:
        enabled: true
      endpoint: http://admin-server:4318/v1/traces
    metrics:
      export:
        enabled: false
  tracing:
    sampling:
      probability: 1.0
  opentelemetry:
    resource-attributes:
      service:
        name: my-agent-service
        version: 1.0.0

# Spring AI 观测配置
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

---

## 4. Admin 中间件依赖

### 4.1 中间件架构

```
┌─────────────────────────────────────────────────────────────┐
│                     Admin Application                        │
└─────────────────────────────────────────────────────────────┘
        │           │           │           │           │
        ▼           ▼           ▼           ▼           ▼
   ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐
   │  MySQL  │ │   ES    │ │  Nacos  │ │  Redis  │ │RocketMQ │
   │         │ │         │ │         │ │         │ │         │
   │业务数据  │ │向量存储  │ │配置中心  │ │缓存/会话 │ │消息队列  │
   └─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘
```

### 4.2 各中间件职责

| 中间件 | 职责 | 数据类型 |
|--------|------|----------|
| MySQL | 业务数据持久化 | Prompt、Dataset、Experiment 等 |
| Elasticsearch | 向量存储、日志检索 | RAG 向量、Trace 数据 |
| Nacos | 配置中心、服务发现 | Prompt 配置、服务注册 |
| Redis | 缓存、会话存储 | 会话状态、临时数据 |
| RocketMQ | 异步消息处理 | 实验任务、事件通知 |

### 4.3 Docker Compose 部署

```yaml
# docker/middleware/docker-compose.yml
version: '3.8'
services:
  mysql:
    image: mysql:8.0
    environment:
      MYSQL_ROOT_PASSWORD: root123
      MYSQL_DATABASE: agent_studio
    ports:
      - "3306:3306"

  elasticsearch:
    image: elasticsearch:8.12.0
    environment:
      - discovery.type=single-node
      - xpack.security.enabled=false
    ports:
      - "9200:9200"

  nacos:
    image: nacos/nacos-server:v2.3.0
    environment:
      MODE: standalone
    ports:
      - "8848:8848"

  redis:
    image: redis:7.2
    ports:
      - "6379:6379"

  rocketmq:
    image: apache/rocketmq:5.1.0
    ports:
      - "9876:9876"
      - "10911:10911"
```

---

## 5. RAG 集成设计

### 5.1 RAG 架构

```
┌─────────────────────────────────────────────────────────────┐
│                      RAG Pipeline                            │
│                                                              │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐              │
│  │ Document │───>│  Splitter │───>│  Indexer │              │
│  │  Loader  │    │          │    │          │              │
│  └──────────┘    └──────────┘    └──────────┘              │
│                                        │                     │
│                                        ▼                     │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐              │
│  │ Retriever│<───│ Vector   │<───│Embedding │              │
│  │          │    │  Store   │    │  Model   │              │
│  └──────────┘    └──────────┘    └──────────┘              │
│       │                                                     │
│       ▼                                                     │
│  ┌──────────┐    ┌──────────┐                              │
│  │ Reranker │───>│ Advisor  │───> LLM Context              │
│  │          │    │          │                              │
│  └──────────┘    └──────────┘                              │
└─────────────────────────────────────────────────────────────┘
```

### 5.2 知识库服务

```java
@Service
public class KnowledgeBaseServiceImpl implements KnowledgeBaseService {

    /**
     * 创建知识库
     */
    public KnowledgeBase create(KnowledgeBaseCreateRequest request);

    /**
     * 文档索引管道
     */
    public void indexDocuments(String kbId, List<Document> documents);

    /**
     * 检索相关文档
     */
    public List<DocumentChunk> retrieve(String kbId, String query, int topK);
}
```

### 5.3 向量存储支持

Admin 支持多种向量存储后端：

| 存储类型 | 实现 | 适用场景 |
|----------|------|----------|
| Elasticsearch | ElasticSearchVectorStoreService | 企业级、已有 ES 集群 |
| Milvus | - | 大规模向量检索 |
| PGVector | - | PostgreSQL 生态 |

---

## 6. 工作流引擎设计

### 6.1 工作流架构

```
┌─────────────────────────────────────────────────────────────┐
│                    Workflow Engine                           │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │                    Processors                         │   │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐│   │
│  │  │  Start   │ │   LLM    │ │   MCP    │ │ Parallel ││   │
│  │  │Processor │ │Processor │ │Processor │ │Processor ││   │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘│   │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐│   │
│  │  │  Plugin  │ │Iterator  │ │ Variable │ │  Output  ││   │
│  │  │Processor │ │Processor │ │Processor │ │Processor ││   │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘│   │
│  └──────────────────────────────────────────────────────┘   │
│                            │                                 │
│                            ▼                                 │
│  ┌──────────────────────────────────────────────────────┐   │
│  │                  Workflow Service                     │   │
│  │  - 流程编排                                            │   │
│  │  - 状态管理                                            │   │
│  │  - 条件路由                                            │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### 6.2 处理器类型

| 处理器 | 类 | 功能 |
|--------|-----|------|
| StartExecuteProcessor | 启动节点 | 工作流入口 |
| ParallelExecuteProcessor | 并行节点 | 并行执行多分支 |
| IteratorStartExecuteProcessor | 迭代节点 | 循环处理 |
| MCPExecuteProcessor | MCP 节点 | MCP 工具调用 |
| PluginExecuteProcessor | 插件节点 | 自定义插件执行 |
| OutputExecuteProcessor | 输出节点 | 结果输出 |

### 6.3 工作流执行器

```java
@Service
public class WorkflowAgentExecutor extends AbstractAgentExecutor {

    @Override
    protected Flux<NodeOutput> doExecute(AgentContext context) {
        // 解析工作流定义
        Workflow workflow = parseWorkflow(context);

        // 按拓扑顺序执行节点
        return executeNodes(workflow, context);
    }

    private Flux<NodeOutput> executeNodes(Workflow workflow, AgentContext context) {
        return Flux.fromIterable(workflow.getNodes())
            .flatMap(node -> executeNode(node, context));
    }
}
```
