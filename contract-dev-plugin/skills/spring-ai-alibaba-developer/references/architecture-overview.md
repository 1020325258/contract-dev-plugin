# Spring AI Alibaba 架构总览

## 1. 整体架构

Spring AI Alibaba 采用分层架构设计，从底层运行时到上层应用平台，各层职责清晰、模块解耦。

```
┌─────────────────────────────────────────────────────────────────┐
│                      应用层 (Application)                        │
│  ┌───────────────────────┐    ┌───────────────────────────────┐ │
│  │   spring-ai-alibaba-  │    │   spring-ai-alibaba-admin     │ │
│  │       studio          │    │   (AI Agent 开发与评估平台)    │ │
│  │   (嵌入式调试 UI)      │    │                               │ │
│  └───────────────────────┘    └───────────────────────────────┘ │
├─────────────────────────────────────────────────────────────────┤
│                      框架层 (Framework)                          │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │            spring-ai-alibaba-agent-framework              │  │
│  │         (Multi-Agent 编排框架，提供多种编排模式)            │  │
│  └───────────────────────────────────────────────────────────┘  │
├─────────────────────────────────────────────────────────────────┤
│                      核心层 (Core)                               │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │              spring-ai-alibaba-graph-core                 │  │
│  │        (图工作流引擎，状态管理，持久化，执行引擎)            │  │
│  └───────────────────────────────────────────────────────────┘  │
├─────────────────────────────────────────────────────────────────┤
│                      集成层 (Integration)                        │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌───────────┐ │
│  │ starter-    │ │ starter-    │ │ starter-    │ │ starter-  │ │
│  │ a2a-nacos   │ │ builtin-    │ │ config-     │ │ graph-    │ │
│  │             │ │ nodes       │ │ nacos       │ │ observation│ │
│  │ (A2A 协议)  │ │ (内置节点)  │ │ (动态配置)  │ │ (可观测性) │ │
│  └─────────────┘ └─────────────┘ └─────────────┘ └───────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

## 2. 模块职责

### 2.1 Graph Core (核心层)

**定位**: 工作流编排引擎，Agent Framework 的底层核心。

**核心职责**:
- 图结构定义与编译 (StateGraph, CompiledGraph)
- 状态管理与合并策略 (OverAllState, KeyStrategy)
- 节点执行与流转控制 (GraphRunner, NodeExecutor)
- 持久化支持 (Checkpoint, BaseCheckpointSaver)
- 并行执行能力 (ParallelNode, ConditionalParallelNode)

**技术栈**: Java 17, Project Reactor, Jackson

### 2.2 Agent Framework (框架层)

**定位**: Multi-Agent 编排框架，提供丰富的 Agent 编排模式。

**核心职责**:
- Agent 基础抽象 (Agent, BaseAgent, ReactAgent)
- 流程编排模式 (Sequential, Parallel, Loop, Supervisor, LlmRouting)
- Hook 与拦截器机制
- 上下文工程 (Human-in-the-loop, 压缩, 编辑)
- 工具调用管理

**依赖**: 基于 Graph Core 构建

### 2.3 Integration (集成层)

**定位**: 提供 Spring Boot Starters，集成外部组件与服务。

**核心模块**:
| Starter | 功能 |
|---------|------|
| a2a-nacos | Agent 间通信协议，Nacos 服务发现与注册 |
| builtin-nodes | 内置工作流节点库 (LLM, Tool, HTTP, RAG 等) |
| config-nacos | 基于 Nacos 的动态配置，无代码构建 Agent |
| graph-observation | 基于 Micrometer/OpenTelemetry 的可观测性 |

### 2.4 Studio & Admin (应用层)

**Studio**: 嵌入式 Agent 调试 UI
- 提供可视化对话调试界面
- 支持 SSE 流式输出
- 会话管理与恢复

**Admin**: AI Agent 开发与评估平台
- Prompt 管理 (版本控制、调试)
- 数据集管理与评估器配置
- 实验执行与结果分析
- 可观测性追踪

## 3. 模块间依赖关系

```
                    ┌─────────────────┐
                    │     Studio      │
                    │     Admin       │
                    └────────┬────────┘
                             │ 使用
                             ▼
┌─────────────────────────────────────────────────────┐
│                Agent Framework                       │
│  (Sequential, Parallel, Loop, Supervisor, Routing)  │
└───────────────────────┬─────────────────────────────┘
                        │ 构建
                        ▼
┌─────────────────────────────────────────────────────┐
│                   Graph Core                         │
│  (StateGraph, CompiledGraph, Checkpoint, Runner)    │
└───────────────────────┬─────────────────────────────┘
                        │ 集成
                        ▼
┌───────────┬───────────┬───────────┬─────────────────┐
│ A2A       │ Builtin   │ Config    │ Observation     │
│ Nacos     │ Nodes     │ Nacos     │                 │
└───────────┴───────────┴───────────┴─────────────────┘
```

**依赖说明**:
1. **Agent Framework → Graph Core**: 所有 FlowAgent 最终都通过构建 StateGraph 实现
2. **Studio/Admin → Agent Framework**: 应用层调用 Agent API 执行业务逻辑
3. **Integration → Graph Core**: Starters 提供 Graph Core 所需的扩展能力
4. **A2A Nacos ↔ Agent Framework**: 双向依赖，Agent 可作为服务提供者或消费者

## 4. 核心数据流

### 4.1 Agent 执行流程

```
用户请求
    │
    ▼
┌─────────────┐
│  Studio/    │  REST API / SSE
│  Admin      │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  Agent      │  流程编排
│  Framework  │  (Sequential/Parallel/...)
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  Graph      │  节点执行、状态管理
│  Core       │  (StateGraph → CompiledGraph)
└──────┬──────┘
       │
       ├─────────────────┐
       │                 │
       ▼                 ▼
┌─────────────┐   ┌─────────────┐
│ LLM 调用    │   │ Tool 调用   │
│ (DashScope) │   │ (MCP/HTTP)  │
└─────────────┘   └─────────────┘
       │                 │
       └────────┬────────┘
                │
                ▼
         持久化 (Checkpoint)
                │
                ▼
          响应返回
```

### 4.2 A2A 远程调用流程

```
Agent A                    Nacos                    Agent B
   │                         │                         │
   │  1. 注册 AgentCard      │                         │
   │────────────────────────►│                         │
   │                         │                         │
   │                         │  2. 注册 AgentCard      │
   │                         │◄────────────────────────│
   │                         │                         │
   │  3. 发现 Agent B        │                         │
   │────────────────────────►│                         │
   │                         │                         │
   │  4. 返回 AgentCard      │                         │
   │◄────────────────────────│                         │
   │                         │                         │
   │  5. JSON-RPC 调用       │                         │
   │─────────────────────────────────────────────────►│
   │                         │                         │
   │  6. 返回结果            │                         │
   │◄─────────────────────────────────────────────────│
```

## 5. 核心概念说明

### 5.1 Graph Core 核心概念

| 概念 | 说明 |
|------|------|
| StateGraph | 状态图定义，管理节点和边的添加 |
| CompiledGraph | 编译后的可执行图 |
| OverAllState | 统一状态容器，存储执行过程中的所有数据 |
| Node | 执行节点，封装业务逻辑动作 |
| Edge | 边，定义节点间的连接和路由条件 |
| Checkpoint | 检查点，持久化执行状态快照 |
| Command | 命令对象，用于条件路由和状态更新 |

### 5.2 Agent Framework 核心概念

| 概念 | 说明 |
|------|------|
| Agent | 所有智能体的抽象基类 |
| BaseAgent | 可转换为 Graph Node 的 Agent |
| ReactAgent | ReAct 模式的智能体 |
| FlowAgent | 流程编排 Agent，支持多种编排模式 |
| Hook | 拦截点，用于消息处理、模型调用控制 |
| Interceptor | 工具调用和模型调用的拦截器链 |

### 5.3 Integration 核心概念

| 概念 | 说明 |
|------|------|
| A2A (Agent-to-Agent) | Agent 间通信协议 |
| AgentCard | Agent 元数据描述，包含能力、端点等信息 |
| AgentRegistry | Agent 注册中心接口 |
| BuiltinNode | 内置工作流节点，开箱即用 |
| Observation | 可观测性，追踪、指标、日志 |

## 6. 技术栈概览

| 层级 | 技术栈 |
|------|--------|
| 应用层 | Spring Boot 3.x, React 19, Next.js 15, TypeScript |
| 框架层 | Spring AI 1.1.x, Project Reactor |
| 核心层 | Java 17, Jackson, Reactor |
| 集成层 | Nacos, OpenTelemetry, Micrometer |
| 存储 | PostgreSQL, MySQL, Oracle, MongoDB, Redis, File |
| AI 模型 | DashScope, OpenAI, DeepSeek |

## 7. 扩展点

### 7.1 Graph Core 扩展点
- 自定义 `KeyStrategy` 实现状态合并逻辑
- 实现 `BaseCheckpointSaver` 添加新的持久化后端
- 自定义 `AsyncNodeAction` 定义节点执行逻辑

### 7.2 Agent Framework 扩展点
- 继承 `FlowAgent` 实现自定义编排模式
- 实现 `Hook` 接口添加拦截逻辑
- 实现 `Interceptor` 接口控制工具/模型调用

### 7.3 Integration 扩展点
- 实现 `AgentRegistry` 接入其他服务发现组件
- 实现 `BuiltinNode` 添加自定义节点类型
- 实现 `AgentLoader` 自定义 Agent 加载方式
