---
description: 自动对当前分支修改的代码进行 CR 检查，使用 code-review Skill。
allowed-tools: Bash(git status:*), Bash(git diff:*), Bash(git branch:*), Bash(git merge-base:*), Bash(git log:*), Read, Grep, Glob
---

## 当前分支信息
- 当前分支：!`git branch --show-current`
- 未提交改动（工作区 vs HEAD）：!`git status --porcelain`
- 与 master 分叉点：!`git merge-base master HEAD`
- 分支全量 diff（分叉点至 HEAD，已提交部分）：!`git diff $(git merge-base master HEAD) HEAD`
- 未提交改动 diff（工作区未 commit 部分）：!`git diff HEAD`

## 任务
目标：使用我的 **code-review** Skill 审查以上**两段 diff 的合并内容**（分支全量改动 + 未提交改动）。

输出格式：
1. 风险改动的简短摘要
2. 问题清单（问题严重程度：blocker/major/minor）
3. 基于 diff 的具体建议，指出修改的文件和行号范围
4. 如果需要更多上下文，请明确列出你需要打开的文件（避免广泛扫描）。
