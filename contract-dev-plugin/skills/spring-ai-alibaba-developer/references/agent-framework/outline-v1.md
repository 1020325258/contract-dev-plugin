# Spring AI Alibaba Agent Framework - 初步大纲

## 1. 模块概述

Spring AI Alibaba Agent Framework 是一个生产级的 Multi-Agent 编排框架，提供丰富的 Agent 编排模式和上下文工程能力。

### 1.1 核心能力
- 多 Agent 编排模式（Sequential、Parallel、Routing、Loop、Supervisor）
- 图工作流引擎支持（基于 spring-ai-alibaba-graph-core）
- 上下文工程（Human-in-the-loop、上下文压缩、编辑、模型调用限制）
- Hook 机制（消息处理、模型调用、工具调用拦截）
- 持久化支持（PostgreSQL、MySQL、Oracle、MongoDB、Redis、File）
- 流式输出与异步执行

## 2. 核心类层次结构

```
Agent (abstract)
├── BaseAgent (abstract) - 可转换为 Node 的 Agent
│   └── ReactAgent - ReAct 模式的智能体
└── FlowAgent (abstract) - 流程编排 Agent
    ├── SequentialAgent - 顺序执行
    ├── ParallelAgent - 并行执行
    ├── LoopAgent - 循环执行
    ├── SupervisorAgent - 监督者模式
    └── LlmRoutingAgent - LLM 路由模式
```

## 3. 核心组件

### 3.1 Agent 基类
- 路径: `com.alibaba.cloud.ai.graph.agent.Agent`
- 职责: 所有 Agent 的抽象基类，提供通用的执行、流式输出、调度能力

### 3.2 BaseAgent
- 路径: `com.alibaba.cloud.ai.graph.agent.BaseAgent`
- 职责: 可转换为 Graph Node 的 Agent 基类

### 3.3 ReactAgent
- 路径: `com.alibaba.cloud.ai.graph.agent.ReactAgent`
- 职责: ReAct (Reasoning and Acting) 模式的智能体实现

### 3.4 FlowAgent 及其子类
- 路径: `com.alibaba.cloud.ai.graph.agent.flow.agent.*`
- 职责: 多 Agent 编排模式实现

### 3.5 Hook 机制
- 路径: `com.alibaba.cloud.ai.graph.agent.hook.*`
- 职责: 提供拦截点用于消息处理、模型调用控制等

### 3.6 Interceptor 机制
- 路径: `com.alibaba.cloud.ai.graph.agent.interceptor.*`
- 职责: 工具调用和模型调用的拦截器链

## 4. Agent 编排模式

### 4.1 SequentialAgent (顺序编排)
- 按顺序执行多个子 Agent
- 前一个 Agent 的输出可作为后一个 Agent 的输入

### 4.2 ParallelAgent (并行编排)
- 同时执行多个子 Agent
- 提供 MergeStrategy 合并结果
- 支持并发限制 (maxConcurrency)

### 4.3 LoopAgent (循环编排)
- 支持多种循环模式：
  - COUNT: 固定次数循环
  - CONDITION: 条件循环
  - JSON_ARRAY: 数组迭代循环

### 4.4 SupervisorAgent (监督者模式)
- 主 Agent 负责决策路由
- 根据输出决定调用哪个子 Agent 或结束

### 4.5 LlmRoutingAgent (LLM 路由模式)
- 使用 LLM 自动选择合适的子 Agent

## 5. 辅助组件

### 5.1 Node 组件
- AgentLlmNode: LLM 调用节点
- AgentToolNode: 工具调用节点

### 5.2 工具相关
- AsyncToolCallback: 异步工具回调
- CancellableAsyncToolCallback: 可取消的异步工具回调

### 5.3 A2A (Agent-to-Agent)
- A2aRemoteAgent: 远程 Agent 调用
- AgentCardProvider: Agent 卡片提供者

## 6. 设计模式应用

### 6.1 Builder 模式
- 所有 Agent 使用 Builder 模式构建
- 类型安全的泛型 Builder 继承

### 6.2 策略模式
- MergeStrategy: 并行结果合并策略
- LoopStrategy: 循环策略

### 6.3 模板方法模式
- FlowAgent.buildSpecificGraph(): 子类实现具体图构建

### 6.4 拦截器模式
- InterceptorChain: 拦截器链
- Hook 机制: 多位置拦截

## 7. 文件结构

```
spring-ai-alibaba-agent-framework/
├── src/main/java/com/alibaba/cloud/ai/graph/agent/
│   ├── Agent.java                    # Agent 基类
│   ├── BaseAgent.java                # 可转换 Node 的 Agent
│   ├── ReactAgent.java               # ReAct Agent
│   ├── flow/                         # 流程编排
│   │   ├── agent/                    # Agent 实现
│   │   │   ├── FlowAgent.java
│   │   │   ├── SequentialAgent.java
│   │   │   ├── ParallelAgent.java
│   │   │   ├── LoopAgent.java
│   │   │   ├── SupervisorAgent.java
│   │   │   └── LlmRoutingAgent.java
│   │   ├── builder/                  # Builder 类
│   │   ├── strategy/                 # 图构建策略
│   │   └── node/                     # 流程节点
│   ├── hook/                         # Hook 机制
│   ├── interceptor/                  # 拦截器
│   ├── node/                         # Agent 节点
│   ├── tool/                         # 工具相关
│   └── a2a/                          # Agent-to-Agent
└── src/test/java/                    # 测试代码
```

## 8. 待深入分析的主题

1. Agent 生命周期管理
2. 状态管理与持久化
3. Hook 与 Interceptor 的协作机制
4. 流式输出实现原理
5. 工具调用流程
6. A2A 远程调用机制
7. 自定义 Agent 扩展点
