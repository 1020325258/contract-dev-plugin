---
description: Spring AI Alibaba 框架开发指南，包含架构理解、系统设计和功能开发指导
---

# Spring AI Alibaba 开发指南

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
| [streaming-output-pattern.md](references/graph-core/streaming-output-pattern.md) | SSE 流式输出集成 |
| [frontend-integration-pattern.md](references/graph-core/frontend-integration-pattern.md) | 前端集成模式 |
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

### 实践经验层（遇到问题时查阅）

| 文档 | 说明 |
|------|------|
| [markstream-sse-integration.md](references/experience/markstream-sse-integration.md) | **markstream-vue 前端对接** - 前端与后端 SSE 对接踩坑记录 |

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
├── architecture-overview.md
├── agent-framework/
│   ├── outline-v1.md
│   ├── core-design.md
│   ├── system-design.md
│   ├── development-guide.md
│   ├── skill.md
│   ├── api-reference.md
│   ├── best-practices.md
│   └── troubleshooting.md
├── graph-core/
│   ├── outline-v1.md
│   ├── core-design.md
│   ├── system-design.md
│   ├── development-guide.md
│   ├── api-reference.md
│   ├── best-practices.md
│   └── troubleshooting.md
├── integration/
│   ├── outline-v1.md
│   ├── core-design.md
│   ├── system-design.md
│   ├── development-guide.md
│   ├── config-reference.md
│   ├── best-practices.md
│   └── troubleshooting.md
└── studio-admin/
    ├── outline-v1.md
    ├── core-design.md
    ├── system-design.md
    ├── development-guide.md
    ├── deployment-guide.md
    ├── best-practices.md
    ├── troubleshooting.md
    └── experience/
        └── markstream-sse-integration.md
```