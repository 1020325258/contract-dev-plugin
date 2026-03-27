---
description: Spring AI Alibaba 框架开发指南，包含架构理解、系统设计和功能开发指导
---

# Spring AI Alibaba 开发指南

## 使用说明

在 Spring AI Alibaba 框架进行开发时，**必须优先查阅本指南**。本指南提供了框架的整体架构、模块职责、核心概念和开发指南，帮助开发者快速理解和正确使用框架。

## 前置要求

- 了解 Spring Boot 3.x 基础（自动配置、Starter 机制）
- 了解 Spring AI 基础概念（ChatModel、Prompt、Tool 等）
- JDK 17+ 开发环境
- 熟悉 Project Reactor 响应式编程（可选，用于深入理解）

## 禁止耗时操作

**严禁**在开发过程中进行以下耗时操作：
- 搜索本地 Maven 仓库（`~/.m2`）
- 下载依赖或反编译 JAR 包
- 如需了解类或方法签名，只允许在项目源码目录内搜索

---

## 架构总览

Spring AI Alibaba 采用分层架构设计，从底层运行时到上层应用平台，各层职责清晰。

```
应用层: Studio (调试 UI) + Admin (开发评估平台)
          ↓
框架层: Agent Framework (Multi-Agent 编排)
          ↓
核心层: Graph Core (图工作流引擎)
          ↓
集成层: A2A Nacos | Builtin Nodes | Config Nacos | Observation
```

**详细架构说明**: [architecture-overview.md](references/architecture-overview.md)

---

## 模块开发指南

### Agent Framework

Multi-Agent 编排框架，提供丰富的 Agent 编排模式。

**核心能力**:
- 5 种编排模式: Sequential、Parallel、Loop、Supervisor、LlmRouting
- 上下文工程: Human-in-the-loop、压缩、编辑
- Hook 与拦截器机制

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

**核心类路径**:
- `com.alibaba.cloud.ai.graph.agent.Agent` - Agent 基类
- `com.alibaba.cloud.ai.graph.agent.flow.agent.*` - 编排模式实现
- `com.alibaba.cloud.ai.graph.agent.hook.*` - Hook 机制

---

### Graph Core

图工作流执行引擎，Agent Framework 的底层核心。

**核心能力**:
- 图结构定义与编译
- 状态管理与合并策略
- 持久化支持 (PostgreSQL、MySQL、MongoDB、Redis 等)
- 并行执行与条件路由

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

**核心类路径**:
- `com.alibaba.cloud.ai.graph.StateGraph` - 状态图定义
- `com.alibaba.cloud.ai.graph.CompiledGraph` - 编译后可执行图
- `com.alibaba.cloud.ai.graph.OverAllState` - 状态容器
- `com.alibaba.cloud.ai.graph.checkpoint.*` - 持久化

---

### Integration (A2A/Nacos)

集成层，提供 Spring Boot Starters。

**包含模块**:
| Starter | 功能 |
|---------|------|
| a2a-nacos | Agent 间通信协议，Nacos 服务发现 |
| builtin-nodes | 内置工作流节点 (17+ 节点类型) |
| config-nacos | 动态配置，无代码构建 Agent |
| graph-observation | 可观测性集成 |

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

**核心类路径**:
- `com.alibaba.cloud.ai.a2a.*` - A2A 协议实现
- `com.alibaba.cloud.ai.node.*` - 内置节点

---

### Studio & Admin

应用层，提供可视化开发与调试工具。

**Studio**: 嵌入式 Agent 调试 UI
- Next.js 15 + React 19 前端
- SSE 流式输出
- 会话管理与恢复

**Admin**: AI Agent 开发与评估平台
- Prompt 管理（版本控制、调试）
- 数据集管理与评估
- 实验执行与分析
- 可观测性追踪

**文档索引**:
| 文档 | 说明 |
|------|------|
| [outline-v1.md](references/studio-admin/outline-v1.md) | 模块大纲 |
| [core-design.md](references/studio-admin/core-design.md) | 核心设计分析 |
| [system-design.md](references/studio-admin/system-design.md) | 系统设计 |
| [development-guide.md](references/studio-admin/development-guide.md) | 开发指南 |
| [deployment-guide.md](references/studio-admin/deployment-guide.md) | 部署指南 |
| [best-practices.md](references/studio-admin/best-practices.md) | 最佳实践 |
| [troubleshooting.md](references/studio-admin/troubleshooting.md) | 故障排查 |
| [observability-guide.md](references/studio-admin/observability-guide.md) | **Agent 观测能力增强** - 观测方案对比与实施路径 |

**核心类路径**:
- `com.alibaba.cloud.ai.agent.studio.*` - Studio 后端
- `com.alibaba.cloud.ai.studio.admin.*` - Admin 后端

---

## 快速开始

### 1. 添加依赖

```xml
<dependency>
    <groupId>com.alibaba.cloud.ai</groupId>
    <artifactId>spring-ai-alibaba-starter-graph-observation</artifactId>
</dependency>
```

### 2. 创建简单 Agent

```java
ReactAgent agent = ReactAgent.builder()
    .name("my-agent")
    .chatModel(chatModel)
    .tools(myTools)
    .build();

// 同步执行
AgentExecution execution = agent.call(input);
// 流式执行
Flux<AgentExecution> stream = agent.stream(input);
```

### 3. 创建顺序编排

```java
SequentialAgent agent = SequentialAgent.builder()
    .name("sequential-agent")
    .agents(agent1, agent2, agent3)
    .build();
```

### 4. 持久化配置

```java
CompileConfig config = CompileConfig.builder()
    .checkpointSaver(new PostgresSaver(dataSource))
    .build();
```

---

## 开发工作流

### 功能开发流程

1. **确定需求范围**: 明确功能属于哪个模块
2. **查阅对应模块文档**: 阅读模块的 core-design 和 system-design
3. **参考 API 文档**: 查看 api-reference 了解接口定义
4. **遵循开发规范**: 参考 development-guide 中的最佳实践
5. **测试验证**: 编写单元测试和集成测试

### 常见开发场景

| 场景 | 参考文档 |
|------|----------|
| 创建自定义 Agent | [agent-framework/development-guide.md](references/agent-framework/development-guide.md) |
| 实现自定义编排模式 | [agent-framework/core-design.md](references/agent-framework/core-design.md) |
| 添加持久化支持 | [graph-core/development-guide.md](references/graph-core/development-guide.md) |
| 配置 A2A 通信 | [integration/development-guide.md](references/integration/development-guide.md) |
| 添加自定义节点 | [integration/development-guide.md](references/integration/development-guide.md) |
| 部署 Admin 平台 | [studio-admin/deployment-guide.md](references/studio-admin/deployment-guide.md) |

---

## 参考文档索引

### 按模块索引

```
references/
├── architecture-overview.md          # 架构总览
├── agent-framework/
│   ├── outline-v1.md                 # 模块大纲
│   ├── core-design.md                # 核心设计
│   ├── system-design.md              # 系统设计
│   ├── development-guide.md          # 开发指南
│   ├── skill.md                      # Skill 能力
│   ├── api-reference.md              # API 参考
│   ├── best-practices.md             # 最佳实践
│   └── troubleshooting.md            # 故障排查
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
    └── troubleshooting.md
```

### 按文档类型索引

| 类型 | 说明 |
|------|------|
| outline-v1.md | 模块初步大纲，列出核心类和组件清单 |
| core-design.md | 核心设计分析，深入解析设计原理 |
| system-design.md | 系统设计，描述组件协作和流程 |
| development-guide.md | 开发指南，提供代码示例和最佳实践 |
| api-reference.md | API 参考，详细接口文档 |
| config-reference.md | 配置参考，配置项清单和示例 |
| deployment-guide.md | 部署指南，运维相关说明 |
| best-practices.md | 最佳实践，开发经验总结 |
| troubleshooting.md | 故障排查，常见问题与解决方案 |
| best-practices.md | 最佳实践，开发经验总结 |
| troubleshooting.md | 故障排查，常见问题与解决方案 |

---

## 注意事项

1. **Agent 与 Graph 的关系**: 所有 FlowAgent 最终都通过构建 StateGraph 实现
2. **状态管理**: 使用 OverAllState 统一管理状态，注意 KeyStrategy 的选择
3. **持久化**: 生产环境务必配置持久化，避免状态丢失
4. **流式输出**: 使用 `stream()` 方法获取响应式流
5. **Hook 时机**: 根据需求选择合适的 Hook 位置进行拦截
