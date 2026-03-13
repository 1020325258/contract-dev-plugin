# Spring AI Alibaba Studio & Admin 模块初步大纲

## 1. 模块概述

### 1.1 spring-ai-alibaba-studio
- **定位**: 嵌入式 Agent 调试 UI
- **核心功能**: 为开发者提供可视化的 Agent 对话调试界面
- **部署模式**: 嵌入模式 / 独立模式

### 1.2 spring-ai-alibaba-admin
- **定位**: AI Agent 开发与评估平台
- **核心功能**: Prompt 管理、数据集管理、评估器管理、实验管理、可观测性
- **架构**: 多模块架构

## 2. 目录结构

### 2.1 Studio 目录结构
```
spring-ai-alibaba-studio/
├── agent-chat-ui/           # Next.js 15 前端
│   ├── src/                 # React 组件源码
│   │   ├── providers/       # 状态管理 Providers
│   │   ├── components/      # UI 组件
│   │   ├── lib/             # API 客户端
│   │   └── types/           # TypeScript 类型定义
│   ├── package.json
│   └── next.config.mjs
├── src/main/java/
│   └── com/alibaba/cloud/ai/agent/studio/
│       ├── controller/      # REST API 控制器
│       │   ├── AgentController.java
│       │   ├── ThreadController.java
│       │   └── ExecutionController.java
│       ├── loader/          # Agent 加载机制
│       │   ├── AgentLoader.java
│       │   ├── AgentStaticLoader.java
│       │   └── ConfigAgentWatcher.java
│       ├── service/         # 业务服务
│       │   ├── RunnerService.java
│       │   └── ThreadService.java
│       ├── dto/             # 数据传输对象
│       ├── config/          # 配置类
│       └── tracing/         # 追踪相关
└── pom.xml
```

### 2.2 Admin 目录结构
```
spring-ai-alibaba-admin/
├── frontend/                # 前端应用
├── spring-ai-alibaba-admin-server-core/    # 核心业务逻辑
│   └── src/main/java/com/alibaba/cloud/ai/studio/core/
│       ├── agent/           # Agent 执行器
│       ├── rag/             # RAG 相关
│       ├── workflow/        # 工作流处理
│       └── base/service/    # 基础服务实现
├── spring-ai-alibaba-admin-server-openapi/ # OpenAPI 接口
├── spring-ai-alibaba-admin-server-runtime/ # 运行时
├── spring-ai-alibaba-admin-server-start/   # 启动模块
│   └── src/main/java/com/alibaba/cloud/ai/studio/admin/
│       ├── controller/      # REST 控制器
│       │   ├── PromptController.java
│       │   ├── DatasetController.java
│       │   ├── ExperimentController.java
│       │   ├── EvaluatorController.java
│       │   ├── ModelConfigController.java
│       │   └── ObservabilityController.java
│       └── service/         # 业务服务
├── deploy/                  # 部署配置
├── docker/                  # Docker 配置
└── docs/                    # 文档
```

## 3. 核心组件识别

### 3.1 Studio 核心组件

| 组件 | 类型 | 职责 |
|------|------|------|
| AgentController | @RestController | 列出可用 Agent 应用 |
| ThreadController | @RestController | 会话管理 CRUD |
| ExecutionController | @RestController | Agent 执行（SSE 流式） |
| AgentLoader | Interface | Agent 加载接口 |
| AgentStaticLoader | @Component | 静态 Agent 加载实现 |
| ThreadService | Interface | 会话服务接口 |

### 3.2 Admin 核心组件

| 组件 | 类型 | 职责 |
|------|------|------|
| PromptController | @RestController | Prompt 管理与调试 |
| DatasetController | @RestController | 数据集管理 |
| ExperimentController | @RestController | 实验执行管理 |
| EvaluatorController | @RestController | 评估器管理 |
| ModelConfigController | @RestController | 模型配置管理 |
| ObservabilityController | @RestController | 可观测性追踪 |
| BasicAgentExecutor | @Service | 基础 Agent 执行器 |
| WorkflowAgentExecutor | @Service | 工作流 Agent 执行器 |

## 4. API 端点汇总

### 4.1 Studio API
| 端点 | 方法 | 描述 |
|------|------|------|
| `/list-apps` | GET | 列出可用 Agent |
| `/apps/{appName}/users/{userId}/threads` | GET/POST | 会话列表/创建 |
| `/apps/{appName}/users/{userId}/threads/{threadId}` | GET/DELETE | 会话详情/删除 |
| `/run_sse` | POST | SSE 流式运行 Agent |
| `/resume_sse` | POST | HitL 反馈后恢复执行 |

### 4.2 Admin API
| 端点 | 方法 | 描述 |
|------|------|------|
| `/api/prompt` | GET/POST/PUT/DELETE | Prompt CRUD |
| `/api/prompt/version` | GET/POST | Prompt 版本管理 |
| `/api/prompt/run` | POST | Prompt 调试运行 |
| `/api/prompts` | GET | Prompt 列表 |
| `/api/dataset/*` | * | 数据集管理 |
| `/api/experiment/*` | * | 实验管理 |
| `/api/evaluator/*` | * | 评估器管理 |

## 5. 技术栈

### 5.1 Studio 技术栈
- **后端**: Spring Boot 3.x, Spring WebFlux (Reactor)
- **前端**: Next.js 15, React 19, TypeScript
- **通信**: SSE (Server-Sent Events)
- **样式**: Tailwind CSS, Radix UI

### 5.2 Admin 技术栈
- **后端**: Spring Boot 3.x, MyBatis Plus
- **前端**: React
- **中间件**: MySQL, Elasticsearch, Nacos, Redis, RocketMQ
- **可观测性**: OpenTelemetry, Micrometer

---

## 6. 差距分析检查清单

### 6.1 已分析的类/接口

#### Studio 模块
| 类/接口 | 状态 | 说明 |
|---------|------|------|
| AgentLoader | 已分析 | Agent 加载核心接口 |
| AgentStaticLoader | 已分析 | 静态加载实现 |
| ConfigAgentWatcher | 已分析 | 配置文件监听 |
| AgentController | 已分析 | Agent 列表 API |
| ThreadController | 已分析 | 会话管理 API |
| ExecutionController | 已分析 | SSE 执行 API |
| ThreadService | 已分析 | 会话服务接口 |
| ThreadServiceImpl | 已分析 | 内存存储实现（生产需替换） |
| WebConfig | 已分析 | CORS 配置，条件加载 |
| SaaStudioWebModuleAutoConfiguration | 已分析 | 自动配置类 |

#### Admin 模块
| 类/接口 | 状态 | 说明 |
|---------|------|------|
| PromptController | 已分析 | Prompt 管理 |
| DatasetController | 已分析 | 数据集管理 |
| ExperimentController | 已分析 | 实验管理 |
| EvaluatorController | 已分析 | 评估器管理 |
| ModelConfigController | 已分析 | 模型配置 |
| ObservabilityController | 已分析 | 可观测性 |
| AbstractAgentExecutor | 已分析 | 执行器基类 |
| BasicAgentExecutor | 已分析 | 基础执行器 |
| WorkflowAgentExecutor | 已分析 | 工作流执行器 |
| JudgeOperator | 已分析 | 条件判断操作符枚举 |
| KnowledgeBaseServiceImpl | 已分析 | 知识库服务 |
| VectorStoreFactory | 已分析 | 向量存储工厂 |

### 6.2 已覆盖的配置项

| 配置项 | 文档位置 |
|--------|----------|
| CORS 配置 | development-guide.md |
| OTel 配置 | deployment-guide.md, development-guide.md |
| Nacos 配置 | development-guide.md, deployment-guide.md |
| 模型配置 | deployment-guide.md |
| 中间件配置 | deployment-guide.md |

### 6.3 已说明的设计决策

| 设计决策 | 说明 |
|----------|------|
| 嵌入式 UI 设计 | core-design.md |
| SSE 流式通信 | core-design.md, system-design.md |
| 内存会话存储 | best-practices.md（生产建议替换） |
| 多租户设计 | system-design.md |
| HitL 工作流 | core-design.md |

### 6.4 已提及的扩展点

| 扩展点 | 说明 |
|--------|------|
| AgentLoader 接口 | 自定义 Agent 注册 |
| ThreadService 接口 | 自定义会话存储 |
| Evaluator 接口 | 自定义评估器 |
| ExecuteProcessor 接口 | 自定义工作流节点 |
| ToolCallback 构建 | 自定义工具 |

### 6.5 遗漏项补充

以下内容已在迭代 2 中补充：

1. **JudgeOperator 枚举** - 工作流条件判断操作符，已在 best-practices.md 中详细说明
2. **WebConfig 条件加载** - `@ConditionalOnProperty` 控制是否启用 CORS
3. **ThreadServiceImpl 内存存储限制** - 已在 troubleshooting.md 中说明生产环境建议
4. **更多代码示例** - 已在 best-practices.md 和 troubleshooting.md 中补充
