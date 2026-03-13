# Spring AI Alibaba Integration 模块研究大纲

## 1. 模块概览

### 1.1 负责模块
- **spring-ai-alibaba-starter-a2a-nacos**: A2A 协议集成，支持 Agent 间通信
- **spring-ai-alibaba-starter-builtin-nodes**: 内置工作流节点库
- **spring-ai-alibaba-starter-config-nacos**: Nacos 动态配置集成
- **spring-ai-alibaba-starter-graph-observation**: 可观测性集成

### 1.2 示例模块
- **chatbot**: 聊天机器人示例
- **deepresearch**: 深度研究 Agent 示例
- **documentation**: 完整文档示例（框架教程、Graph 示例）

---

## 2. A2A Nacos Starter

### 2.1 目录结构
```
spring-ai-alibaba-starter-a2a-nacos/
├── src/main/java/com/alibaba/cloud/ai/a2a/
│   ├── autoconfigure/           # 自动配置
│   │   ├── A2aServerProperties.java
│   │   ├── A2aAgentCardProperties.java
│   │   ├── client/
│   │   │   └── A2aClientAgentCardProviderAutoConfiguration.java
│   │   ├── server/
│   │   │   ├── A2aServerAutoConfiguration.java
│   │   │   ├── A2aServerHandlerAutoConfiguration.java
│   │   │   └── A2aServerAgentCardAutoConfiguration.java
│   │   └── nacos/
│   │       ├── NacosA2aDiscoveryAutoConfiguration.java
│   │       └── NacosA2aRegistryAutoConfiguration.java
│   ├── core/                    # 核心实现
│   │   ├── constants/
│   │   ├── registry/
│   │   ├── route/
│   │   └── server/
│   └── registry/nacos/          # Nacos 注册中心集成
│       ├── discovery/
│       ├── properties/
│       ├── register/
│       └── service/
```

### 2.2 核心配置类

| 配置类 | 功能 |
|--------|------|
| A2aServerProperties | A2A 服务器配置属性 |
| NacosA2aProperties | Nacos 连接配置属性 |
| A2aServerAutoConfiguration | A2A 服务器自动配置 |
| NacosA2aDiscoveryAutoConfiguration | Nacos 服务发现配置 |
| NacosA2aRegistryAutoConfiguration | Nacos 服务注册配置 |

### 2.3 核心组件

| 组件 | 说明 |
|------|------|
| AgentRegistry | Agent 注册接口 |
| NacosAgentRegistry | Nacos 实现的 Agent 注册 |
| NacosAgentCardProvider | 从 Nacos 获取 AgentCard |
| JsonRpcA2aRequestHandler | JSON-RPC 请求处理器 |
| GraphAgentExecutor | Graph Agent 执行器 |

---

## 3. Builtin Nodes Starter

### 3.1 内置节点清单

| 节点类 | 功能描述 |
|--------|----------|
| LlmNode | LLM 调用节点 |
| AgentNode | Agent 调用节点 |
| AnswerNode | 直接回答节点 |
| HumanNode | 人工介入节点 |
| ToolNode | 工具调用节点 |
| McpNode | MCP 协议节点 |
| HttpNode | HTTP 请求节点 |
| KnowledgeRetrievalNode | 知识检索节点 |
| QuestionClassifierNode | 问题分类节点 |
| TemplateTransformNode | 模板转换节点 |
| AssignerNode | 变量赋值节点 |
| VariableAggregatorNode | 变量聚合节点 |
| ListOperatorNode | 列表操作节点 |
| IterationNode | 迭代节点 |
| DocumentExtractorNode | 文档提取节点 |
| ParameterParsingNode | 参数解析节点 |
| CodeExecutorNodeAction | 代码执行节点 |

### 3.2 代码执行支持

- **LocalCommandlineCodeExecutor**: 本地命令行执行
- **DockerCodeExecutor**: Docker 容器执行
- 支持语言: Java, Python3, JavaScript

---

## 4. Config Nacos Starter

### 4.1 功能特点
- 无代码构建 Agent
- YAML 格式配置
- Nacos 动态配置集成
- 配置热更新

### 4.2 核心组件

| 组件 | 说明 |
|------|------|
| NacosAgentConfig | 配置加载 |
| NacosAgentBuilderFactory | Agent 构建工厂 |
| NacosReactAgentBuilder | React Agent 构建器 |
| NacosMcpToolsInjector | MCP 工具注入 |
| NacosModelInjector | 模型注入 |
| NacosPromptInjector | Prompt 注入 |

---

## 5. Graph Observation Starter

### 5.1 功能特点
- 基于 Micrometer 的可观测性
- OpenTelemetry 集成
- 分布式追踪

### 5.2 核心组件

| 组件 | 说明 |
|------|------|
| GraphObservationAutoConfiguration | 自动配置 |
| GraphObservationProperties | 配置属性 |
| SpringAiAlibabaChatModelObservationConvention | 观察约定 |

---

## 6. Examples 示例

### 6.1 框架教程示例 (framework/tutorials)
- AgentsExample: Agent 基础用法
- ToolsExample: 工具使用
- MemoryExample: 记忆管理
- HooksExample: 钩子函数
- ModelsExample: 模型使用
- MessagesExample: 消息处理
- StructuredOutputExample: 结构化输出
- MCP 远程工具示例

### 6.2 高级示例 (framework/advanced)
- MultiAgentExample: 多 Agent 协作
- HumanInTheLoopExample: 人机交互
- ContextEngineeringExample: 上下文工程
- RAGExample: 检索增强生成
- WorkflowExample: 工作流
- A2A Example: Agent 间通信

### 6.3 Graph 示例 (graph/)
- QuickStartExample: 快速开始
- PersistenceExample: 持久化
- StreamingExample: 流式处理
- HumanInTheLoopExample: 人机交互
- MultiAgentSupervisorExample: 多 Agent 监督
- ParallelBranchExample: 并行分支
- SubgraphExample: 子图

---

## 7. 后续文档计划

1. **core-design.md**: 核心设计分析
   - A2A 协议设计
   - Nacos 服务发现机制
   - 可观测性集成设计

2. **system-design.md**: 系统设计
   - Agent 注册与发现
   - 跨 Agent 通信流程
   - 配置热更新机制

3. **development-guide.md**: 功能开发指南
   - 配置方式
   - 代码示例
   - 最佳实践

4. **config-reference.md**: 配置参考
   - 完整配置项清单
   - 配置示例
