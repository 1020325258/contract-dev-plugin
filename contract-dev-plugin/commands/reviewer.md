---
description: 独立的代码审查阶段（Evaluator）。不是自检，而是切换成资深 reviewer 角色挑刺。先只列问题，不立刻修。
allowed-tools: Bash(git status:*), Bash(git diff:*), Bash(git branch:*), Bash(git merge-base:*), Bash(git log:*), Bash(ls:*), Read, Grep, Glob, Agent
---

## 当前分支信息
- 当前分支：!`git branch --show-current`
- 未提交改动（工作区 vs HEAD）：!`git status --porcelain`
- 与 master 分叉点：!`git merge-base master HEAD`
- 分支全量 diff（分叉点至 HEAD，已提交部分）：!`git diff $(git merge-base master HEAD) HEAD`
- 未提交改动 diff（工作区未 commit 部分）：!`git diff HEAD`
- openspec 活跃变更：!`ls openspec/changes/ 2>/dev/null | grep -v archive || echo "无"`

## 任务

**核心理念：自评不可信，必须切换角色。**

代码写完后，不要说"再检查一下有没有问题"，而是切换成明确的 reviewer 角色挑刺。

---

### 阶段一：独立审查（Evaluator）

**切换角色指令：**
> 现在你不是作者，你是资深 reviewer。请从以下 9 个维度审查代码，先只列问题，不要立刻修。

**审查维度：**
1. **并发安全** - 共享变量访问是否加锁、线程池配置、竞态条件
2. **事务边界** - 事务传播级别、长事务风险、事务内调用外部服务
3. **空指针防护** - 方法返回值、集合遍历、Optional 使用
4. **幂等性** - 接口幂等、重复提交、消息消费
5. **异常回滚** - 异常抛出、事务回滚、吞异常
6. **日志规范** - 关键操作日志、敏感信息脱敏、日志级别
7. **监控告警** - 核心指标上报、异常告警、埋点
8. **兼容性** - 接口变更、配置变更、schema 变更
9. **测试覆盖** - 核心逻辑测试、边界条件、遗漏场景

**输出格式：**
```markdown
## 审查报告

### 并发安全
- [问题描述] - 文件:行号

### 事务边界
- [问题描述] - 文件:行号

...（9个维度都要有输出，哪怕没有问题也注明"无"）
```

---

### 阶段二：OpenSpec 文档审查（Agent Team）

**无论 openspec 目录是否有活跃变更，此阶段都必须执行。**

启动两个并行 agent 分工收集信息，主线程对比后输出报告：

**Agent-1（代码阅读者）prompt：**
```
你是代码阅读者。请根据以下 diff 内容，读取本次变更涉及的源码文件，
整理出实际实现的行为，包括：工具/方法的参数名和类型、返回数据结构、核心业务规则、枚举值定义。
只做阅读和整理，不修改任何文件。输出格式：结构化的"代码行为摘要"。

diff 内容：[将阶段一中的 diff 内容传入]
```

**Agent-2（文档审查者）prompt：**
```
你是文档审查者。请读取 openspec/changes/ 下所有非 archive 的变更目录中的文档
（包括 design.md、tasks.md、specs/ 下的规格文件），以及 openspec/specs/ 下的主规格文件。
整理出文档描述的行为，包括：接口参数、返回结构、业务规则、触发条件。
同时检查：tasks.md 中是否有未完成的 - [ ] 任务，是否存在"待定"、"TODO"等模糊描述。
只做阅读和整理，不修改任何文件。输出格式：结构化的"文档描述摘要"。
```

两个 agent 完成后，主线程对比两份摘要，按以下格式输出 OpenSpec 审查报告：

```
## OpenSpec 文档审查报告

### 变更：<change-name>（无活跃变更则注明）

#### ✅ 一致项
#### ⚠️ 不一致项（需修复）
#### 📋 过时内容（需更新）
#### 📝 规范问题
```

> 发现问题时，列出问题清单后询问用户：是修复代码还是修复文档？不要自动修复。
