---
description: Spring AI Alibaba 框架开发指南，包含架构理解、系统设计和功能开发指导
---

# Spring AI Alibaba 开发指南

## 知识索引

### 基础层（必读）
- [RAG 核心概念](./references/foundation/rag-core-concepts.md) - RAG 架构、检索时机、应用场景
- [重排序模型](./references/foundation/rerank-model.md) - Rerank 原理与使用方式

### 领域层（按需查阅）
- [RAG ETL Pipeline](./references/domain/rag-etl-pipeline.md) - 文档读取、转换、分割组件
- [RAG 检索策略](./references/domain/rag-retrieval-strategies.md) - 向量检索、混合检索、HyDE、Query 变换
- [Agent RAG Tool 模式](./references/domain/agent-rag-tool.md) - 将 RAG 封装为 Tool，Agent 智能调用
- [可观测性指南](./references/domain/observability-guide.md) - Zipkin、Langfuse、ARMS 集成
- [模型评估指南](./references/domain/evaluation-guide.md) - 相关性、事实性、正确性评估器

### 实践经验层（遇到问题时查阅）
- [markstream-vue 前端对接](./references/experience/markstream-sse-integration.md) - SSE 流式输出前后端对接踩坑

---

## 模块开发指南

### Agent Framework

**文档索引**:
| 文档 | 说明 |
|------|------|
| [outline-v1.md](references/agent-framework/outline-v1.md) | 模块大纲 |
| [core-design.md](references/agent-framework/core-design.md) | 核心设计分析 |
| [system-design.md](references/agent-framework/system-design.md) | 系统设计 |
| [development-guide.md](references/agent-framework/development-guide.md) | 开发指南 |
| [skill.md](references/agent-framework/skill.md) | **Skill 能力** - Agent 技能扩展机制 |
| [tool-calling.md](references/agent-framework/tool-calling.md) | **Tool Calling** - 工具调用实现机制 |
| [api-reference.md](references/agent-framework/api-reference.md) | API 参考 |
| [best-practices.md](references/agent-framework/best-practices.md) | 最佳实践 |
| [troubleshooting.md](references/agent-framework/troubleshooting.md) | 故障排查 |

---

### Graph Core

**文档索引**:
| 文档 | 说明 |
|------|------|
| [outline-v1.md](references/graph-core/outline-v1.md) | 模块大纲 |
| [core-design.md](references/graph-core/core-design.md) | 核心设计分析 |
| [system-design.md](references/graph-core/system-design.md) | 系统设计 |
| [development-guide.md](references/graph-core/development-guide.md) | 开发指南 |
| [api-reference.md](references/graph-core/api-reference.md) | API 参考 |
| [best-practices.md](references/graph-core/best-practices.md) | 最佳实践 |
| [troubleshooting.md](references/graph-core/troubleshooting.md) | 故障排查 |
| [dispatcher-routing-pattern.md](references/graph-core/dispatcher-routing-pattern.md) | Dispatcher 路由模式 |
| [streaming-output-pattern.md](references/graph-core/streaming-output-pattern.md) | SSE 流式输出集成（FluxConverter、双消息类型设计） |
| [frontend-integration-pattern.md](references/graph-core/frontend-integration-pattern.md) | **前端集成模式** - nodeName 标识、6种渲染样式、完整节点输出序列 |
| [memory-architecture.md](references/graph-core/memory-architecture.md) | 记忆架构设计 |
| [multi-agent-coordination-pattern.md](references/graph-core/multi-agent-coordination-pattern.md) | 多 Agent 协作编排 |

---

### Integration (A2A/Nacos)

**文档索引**:
| 文档 | 说明 |
|------|------|
| [outline-v1.md](references/integration/outline-v1.md) | 模块大纲 |
| [core-design.md](references/integration/core-design.md) | 核心设计分析 |
| [system-design.md](references/integration/system-design.md) | 系统设计 |
| [development-guide.md](references/integration/development-guide.md) | 开发指南 |
| [config-reference.md](references/integration/config-reference.md) | 配置参考 |
| [best-practices.md](references/integration/best-practices.md) | 最佳实践 |
| [troubleshooting.md](references/integration/troubleshooting.md) | 故障排查 |

---

### Studio & Admin

**文档索引**:
| 文档 | 说明 |
|------|------|
| [outline-v1.md](references/studio-admin/outline-v1.md) | 模块大纲 |
| [core-design.md](references/studio-admin/core-design.md) | 核心设计分析 |
| [system-design.md](references/studio-admin/system-design.md) | 系统设计 |
| [development-guide.md](references/studio-admin/development-guide.md) | 开发指南 |
| [deployment-guide.md](references/studio-admin/deployment-guide.md) | 部署指南 |
| [standalone-usage.md](references/studio-admin/standalone-usage.md) | **前端独立使用** |
| [best-practices.md](references/studio-admin/best-practices.md) | 最佳实践 |
| [troubleshooting.md](references/studio-admin/troubleshooting.md) | 故障排查 |
| [observability-guide.md](references/studio-admin/observability-guide.md) | **Agent 观测能力增强** |

---

## 架构总览

```
应用层: Studio (调试 UI) + Admin (开发评估平台)
          ↓
框架层: Agent Framework (Multi-Agent 编排)
          ↓
核心层: Graph Core (图工作流引擎)
          ↓
集成层: A2A Nacos | Builtin Nodes | Config Nacos | Observation
```

---

## 参考文档结构

```
references/
├── foundation/                          # 基础层
│   ├── rag-core-concepts.md
│   └── rerank-model.md
├── domain/                              # 领域层
│   ├── rag-etl-pipeline.md
│   ├── rag-retrieval-strategies.md
│   ├── agent-rag-tool.md
│   ├── observability-guide.md
│   └── evaluation-guide.md
├── experience/                          # 实践经验层
│   └── markstream-sse-integration.md
├── agent-framework/                     # Agent 模块
├── graph-core/                          # Graph 模块
├── integration/                         # 集成模块
└── studio-admin/                        # Studio 模块
```
