---
description: 自动对当前分支修改的代码进行 CR 检查，使用 code-review Skill。
allowed-tools: Bash(git status:*), Bash(git diff:*), Bash(git branch:*), Read, Grep, Glob
---

## 当前分支信息
- 当前分支：!`git branch --show-current`
- 状态：!`git status --porcelain`
- diff（当前修改和 HEAD 的差异）：!`git diff HEAD`

## 任务
目标：使用我的 **code-review** Skill 自动审查以上 diff 中的改动。

输出格式：
1. 风险改动的简短摘要
2. 问题清单（问题严重程度：blocker/major/minor）
3. 基于 diff 的具体建议，指出修改的文件和行号范围
4. 如果需要更多上下文，请明确列出你需要打开的文件（避免广泛扫描）。
