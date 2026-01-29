# CR Plugin

专业的代码 Code Review 插件，支持自定义规范检查和代码解释功能。

## 功能特性

### 1. `/cr` 命令 - 专业代码审查

对指定的代码文件或代码片段进行全面的 Code Review，从多个维度进行深度审查：

- **代码质量**: 检查代码的可读性、可维护性和代码风格是否符合最佳实践
- **潜在问题**: 识别可能的 bug、逻辑错误、边界条件处理不当等问题
- **性能优化**: 发现性能瓶颈和优化建议
- **安全性**: 检查常见安全漏洞，如 SQL 注入、XSS、CSRF 等
- **最佳实践**: 建议更符合行业标准和设计模式的实现方式

### 2. `contract-cr` Skill - 签约项目代码审查规范

专门针对签约项目的代码审查规范，重点关注空指针安全检查。

#### 核心检查项

- **空指针安全**: 检查所有可能返回 null 的方法调用是否使用 `Optional` 包装
- 特别关注 `contractReq.getPromiseInfo()` 等关键方法的空指针安全

#### 输出格式

提供结构化的审查报告，包括：

- 审查概览（文件路径、代码行数、严重程度）
- 通过的检查项
- 需要改进的地方（中等优先级）
- 严重问题（必须修复）
- 代码质量评分
- 改进建议（短期/中期/长期）
- 关键提醒

### 3. `explaining-code` Skill - 代码解释

通过可视化图表和类比来解释代码，帮助理解代码逻辑和工作原理。

#### 解释方式

1. **类比法**: 将代码与日常生活中的事物进行比较
2. **图表展示**: 使用 ASCII 艺术展示流程、结构或关系
3. **逐步讲解**: 一步一步地解释代码执行过程
4. **易错点提示**: 标注常见的错误或误解

## 安装使用

### 安装插件

```bash
# 克隆插件到本地
cd /path/to/your/plugins
git clone <repository-url>

# 或者将插件目录复制到 Claude Code 插件目录
```

### 使用方法

#### 使用 `/cr` 命令

```bash
# 审查指定文件
/cr src/service/ContractService.java

# 审查多个文件
/cr src/service/*.java

# 审查代码片段（在对话中粘贴代码后）
/cr
```

#### 使用 Skills

在对话中，Claude Code 会根据上下文自动调用相应的 skill：

- 当进行签约项目代码审查时，自动使用 `contract-cr` skill
- 当需要解释代码时，自动使用 `explaining-code` skill

你也可以明确要求使用某个 skill：

```
请使用 contract-cr 规范审查这段代码
请用图表解释这个函数的工作原理
```

## 配置说明

插件配置文件位于 `.claude-plugin/plugin.json`：

```json
{
  "name": "cr-plugin",
  "description": "专业的代码 CR 插件，支持自定义规范检查",
  "version": "1.0.0",
  "author": {
    "name": "11来了"
  },
  "commands": [
    "./commands/cr.md"
  ],
  "skills": [
    "./skills/contract-cr"
  ]
}
```

## 目录结构

```
cr-plugin/
├── .claude-plugin/
│   └── plugin.json          # 插件配置文件
├── commands/
│   └── cr.md               # CR 命令定义
├── skills/
│   ├── contract-cr/        # 签约项目 CR 规范 skill
│   │   └── SKILL.md
│   └── explaining-code/    # 代码解释 skill
│       └── SKILL.md
└── README.md               # 本文档
```

## 示例

### 代码审查示例

输入：
```
/cr src/service/ContractService.java
```

输出：
```
### 📋 审查概览
- **审查文件**: src/service/ContractService.java
- **代码行数**: 234
- **审查时间**: 2026-01-17
- **严重程度**: 🔴高危

### ❌ 严重问题（必须修复）

#### 🔴 1. 未使用 Optional 包装可能为 null 的数据
- **位置**: src/service/ContractService.java:89
- **问题**: 直接调用 contractReq.getPromiseInfo() 未使用 Optional 包装
- **风险**: 可能导致 NullPointerException
...
```

### 代码解释示例

输入：
```
请解释这个函数是如何工作的：
[代码片段]
```

输出会包含类比、ASCII 图表、逐步讲解和易错点提示。

## 开发与贡献

### 自定义规范

你可以通过修改或添加 skill 来自定义代码审查规范：

1. 在 `skills/` 目录下创建新的 skill 目录
2. 编写 `SKILL.md` 文件定义审查规则
3. 在 `plugin.json` 中注册新的 skill

### Skill 文件格式

```markdown
---
name: my-custom-cr
description: 自定义代码审查规范
---

# 审查规则

## 检查项 1
- 规则描述
- 检查方法
- 示例代码

## 检查项 2
...
```

## 版本历史

- **v1.0.0** (2026-01-17)
  - 初始版本发布
  - 支持 `/cr` 命令
  - 包含 `contract-cr` 和 `explaining-code` skills

## 作者

**11来了**

## 许可证

MIT License

## 反馈与支持

如有问题或建议，请提交 Issue 或 Pull Request。
