---
description: 自动对当前分支修改的代码进行 CR 检查，使用 reviewer Skill。
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

本次 CR 分两个阶段并行执行：

---

### 阶段一：代码审查（主线程执行）

使用 **reviewer** Skill 审查以上两段 diff 的合并内容（分支全量改动 + 未提交改动）。

输出格式：
1. 风险改动的简短摘要
2. 问题清单（严重程度：blocker / major / minor）
3. 基于 diff 的具体建议，指出修改的文件和行号范围
4. 如果需要更多上下文，请明确列出你需要打开的文件（避免广泛扫描）

---

### 阶段二：OpenSpec 文档审查（Agent Team 执行）

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
