---
description: 独立审查阶段，通过 Agent Team 并行执行代码审查和文档一致性审查。
---

# Reviewer - 独立审查阶段

## 核心职责

1. **代码审查** - 严格检查代码逻辑的准确性（通过 Agent Team 并行执行）
2. **代码与 OpenSpec 文档一致性审查** - 检查过时或不一致的文档，并修复验证

## 审查流程

### 阶段一：代码审查（Agent Team 并行）

启动多个并行 agent 从不同维度审查代码：

- **Agent-1: 并发安全审查** - 共享变量、线程池、竞态条件
- **Agent-2: 事务边界审查** - 事务传播级别、长事务、事务内调用外部服务
- **Agent-3: 空指针防护审查** - Optional 使用、null 检查
- **Agent-4: 幂等性审查** - 接口幂等、重复提交、消息消费
- **Agent-5: 异常处理审查** - 异常抛出、事务回滚、吞异常

### 阶段二：OpenSpec 文档一致性审查（Agent Team 并行）

**无论 openspec 目录是否有活跃变更，此阶段都必须执行。**

- **Agent-6: 代码阅读者** - 整理代码实际实现的行为
- **Agent-7: 文档审查者** - 检查文档与代码一致性、发现过时内容

### 阶段三：修复与验证

发现不一致时，自动进行修复和验证。

## 参考文档

- [OpenSpec 文档与代码一致性审查](./references/workflow/openspec-doc-review.md)
- [集成测试编写规范](./references/workflow/integration-test-principles.md)
