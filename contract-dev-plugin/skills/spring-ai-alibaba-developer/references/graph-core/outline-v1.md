# Graph Core 模块初步大纲

## 1. 模块概述

Spring AI Alibaba Graph Core 是一个基于图结构的工作流执行引擎，提供了状态管理、节点编排、条件路由、并行执行和持久化能力。该模块是实现 Agent Framework 的底层核心引擎。

### 1.1 核心定位
- 工作流编排引擎
- 状态持久化框架
- 支持复杂的有向图执行

### 1.2 技术栈
- Java 17
- Project Reactor (响应式编程)
- Spring Boot 3.x
- Jackson (状态序列化)

## 2. 核心类清单

### 2.1 图定义层
| 类名 | 路径 | 职责 |
|------|------|------|
| `StateGraph` | `com.alibaba.cloud.ai.graph.StateGraph` | 状态图定义，管理节点和边的添加 |
| `CompiledGraph` | `com.alibaba.cloud.ai.graph.CompiledGraph` | 编译后的图，提供执行入口 |
| `Node` | `com.alibaba.cloud.ai.graph.internal.node.Node` | 节点定义，封装执行动作 |
| `Edge` | `com.alibaba.cloud.ai.graph.internal.edge.Edge` | 边定义，表示节点间的连接关系 |
| `EdgeValue` | `com.alibaba.cloud.ai.graph.internal.edge.EdgeValue` | 边的目标值，支持固定目标和条件路由 |

### 2.2 状态管理层
| 类名 | 路径 | 职责 |
|------|------|------|
| `OverAllState` | `com.alibaba.cloud.ai.graph.OverAllState` | 整体状态容器，管理执行状态数据 |
| `KeyStrategy` | `com.alibaba.cloud.ai.graph.KeyStrategy` | 状态键合并策略接口 |
| `KeyStrategyFactory` | `com.alibaba.cloud.ai.graph.KeyStrategyFactory` | 策略工厂，创建键策略映射 |

### 2.3 执行引擎层
| 类名 | 路径 | 职责 |
|------|------|------|
| `GraphRunner` | `com.alibaba.cloud.ai.graph.GraphRunner` | 图执行入口，基于 Reactor |
| `GraphRunnerContext` | `com.alibaba.cloud.ai.graph.GraphRunnerContext` | 执行上下文，管理运行时状态 |
| `MainGraphExecutor` | `com.alibaba.cloud.ai.graph.executor.MainGraphExecutor` | 主执行器，处理节点流转 |
| `NodeExecutor` | `com.alibaba.cloud.ai.graph.executor.NodeExecutor` | 节点执行器，执行单个节点 |

### 2.4 持久化层
| 类名 | 路径 | 职责 |
|------|------|------|
| `BaseCheckpointSaver` | `com.alibaba.cloud.ai.graph.checkpoint.BaseCheckpointSaver` | 检查点保存器接口 |
| `Checkpoint` | `com.alibaba.cloud.ai.graph.checkpoint.Checkpoint` | 检查点，保存执行状态快照 |
| `MemorySaver` | `com.alibaba.cloud.ai.graph.checkpoint.savers.MemorySaver` | 内存持久化实现 |
| `PostgresSaver` | `com.alibaba.cloud.ai.graph.checkpoint.savers.postgresql.PostgresSaver` | PostgreSQL 持久化实现 |
| `MysqlSaver` | `com.alibaba.cloud.ai.graph.checkpoint.savers.mysql.MysqlSaver` | MySQL 持久化实现 |
| `OracleSaver` | `com.alibaba.cloud.ai.graph.checkpoint.savers.oracle.OracleSaver` | Oracle 持久化实现 |
| `MongoSaver` | `com.alibaba.cloud.ai.graph.checkpoint.savers.mongo.MongoSaver` | MongoDB 持久化实现 |
| `RedisSaver` | `com.alibaba.cloud.ai.graph.checkpoint.savers.redis.RedisSaver` | Redis 持久化实现 |
| `FileSystemSaver` | `com.alibaba.cloud.ai.graph.checkpoint.savers.file.FileSystemSaver` | 文件系统持久化实现 |

### 2.5 动作接口层
| 类名 | 路径 | 职责 |
|------|------|------|
| `AsyncNodeAction` | `com.alibaba.cloud.ai.graph.action.AsyncNodeAction` | 异步节点动作接口 |
| `AsyncNodeActionWithConfig` | `com.alibaba.cloud.ai.graph.action.AsyncNodeActionWithConfig` | 带配置的异步节点动作 |
| `AsyncEdgeAction` | `com.alibaba.cloud.ai.graph.action.AsyncEdgeAction` | 异步边动作接口 |
| `AsyncCommandAction` | `com.alibaba.cloud.ai.graph.action.AsyncCommandAction` | 异步命令动作，用于条件路由 |
| `Command` | `com.alibaba.cloud.ai.graph.action.Command` | 命令对象，表示节点跳转和状态更新 |

### 2.6 并行执行层
| 类名 | 路径 | 职责 |
|------|------|------|
| `ParallelNode` | `com.alibaba.cloud.ai.graph.internal.node.ParallelNode` | 并行节点，并发执行多个分支 |
| `ConditionalParallelNode` | `com.alibaba.cloud.ai.graph.internal.node.ConditionalParallelNode` | 条件并行节点，根据条件动态并行执行 |

### 2.7 配置层
| 类名 | 路径 | 职责 |
|------|------|------|
| `CompileConfig` | `com.alibaba.cloud.ai.graph.CompileConfig` | 编译配置 |
| `RunnableConfig` | `com.alibaba.cloud.ai.graph.RunnableConfig` | 运行时配置 |

## 3. 核心概念

### 3.1 图结构
- **START**: 图的起始点
- **END**: 图的结束点
- **Node**: 执行节点，包含业务逻辑
- **Edge**: 连接节点，定义执行流向

### 3.2 状态管理
- **OverAllState**: 统一状态容器
- **KeyStrategy**: 定义状态字段的合并策略
  - `ReplaceStrategy`: 替换策略
  - `AppendStrategy`: 追加策略
  - 自定义策略

### 3.3 执行模型
- **同步执行**: 阻塞等待结果
- **流式执行**: 基于 Reactor 的响应式流
- **并行执行**: 多分支并发执行
- **中断恢复**: 支持执行中断和恢复

### 3.4 持久化机制
- **Checkpoint**: 执行状态快照
- **Thread**: 执行线程标识
- **多种存储后端**: Memory, PostgreSQL, MySQL, Oracle, MongoDB, Redis, File

## 4. 目录结构

```
spring-ai-alibaba-graph-core/
├── src/main/java/com/alibaba/cloud/ai/graph/
│   ├── StateGraph.java              # 状态图定义
│   ├── CompiledGraph.java           # 编译后的图
│   ├── OverAllState.java            # 整体状态
│   ├── GraphRunner.java             # 图执行器
│   ├── GraphRunnerContext.java      # 执行上下文
│   ├── action/                      # 动作接口
│   │   ├── AsyncNodeAction.java
│   │   ├── AsyncEdgeAction.java
│   │   ├── Command.java
│   │   └── ...
│   ├── checkpoint/                  # 持久化
│   │   ├── Checkpoint.java
│   │   ├── BaseCheckpointSaver.java
│   │   └── savers/
│   │       ├── MemorySaver.java
│   │       ├── postgresql/
│   │       ├── mysql/
│   │       ├── oracle/
│   │       ├── mongo/
│   │       ├── redis/
│   │       └── file/
│   ├── executor/                    # 执行器
│   │   ├── BaseGraphExecutor.java
│   │   ├── MainGraphExecutor.java
│   │   └── NodeExecutor.java
│   ├── internal/                    # 内部实现
│   │   ├── node/
│   │   │   ├── Node.java
│   │   │   ├── ParallelNode.java
│   │   │   └── ConditionalParallelNode.java
│   │   └── edge/
│   │       ├── Edge.java
│   │       ├── EdgeValue.java
│   │       └── EdgeCondition.java
│   ├── state/                       # 状态策略
│   │   └── strategy/
│   ├── serializer/                  # 序列化
│   └── observation/                 # 可观测性
└── src/test/java/                   # 测试代码
```

## 5. 后续文档规划

1. **core-design.md**: 核心设计分析
   - Graph 抽象设计
   - 状态管理设计
   - 持久化架构设计

2. **system-design.md**: 系统设计
   - 执行引擎设计
   - 持久化机制
   - 条件路由实现
   - 并行执行实现

3. **development-guide.md**: 功能开发指南
   - 基础图创建
   - 条件路由
   - 并行执行
   - 持久化配置

4. **api-reference.md**: API 参考
   - 核心类 API
   - 配置选项
   - 扩展点
