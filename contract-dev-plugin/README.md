# Contract Dev Plugin

专业的代码开发辅助插件，包含代码审查、代码解释和数据流分析功能。

## 功能特性

### 代码审查功能

#### 1. `/code-review` 命令 - 专业代码审查

对指定的代码文件或代码片段进行全面的 Code Review，从多个维度进行深度审查：

- **代码质量**: 检查代码的可读性、可维护性和代码风格是否符合最佳实践
- **潜在问题**: 识别可能的 bug、逻辑错误、边界条件处理不当等问题
- **性能优化**: 发现性能瓶颈和优化建议
- **安全性**: 检查常见安全漏洞，如 SQL 注入、XSS、CSRF 等
- **最佳实践**: 建议更符合行业标准和设计模式的实现方式

#### 2. `contract-cr` Skill - 签约项目代码审查规范

专门针对签约项目的代码审查规范，重点关注空指针安全检查。

**核心检查项**：
- **空指针安全**: 检查所有可能返回 null 的方法调用是否使用 `Optional` 包装
- 特别关注 `contractReq.getPromiseInfo()` 等关键方法的空指针安全

**输出格式**：
- 审查概览（文件路径、代码行数、严重程度）
- 通过的检查项
- 需要改进的地方（中等优先级）
- 严重问题（必须修复）
- 代码质量评分
- 改进建议（短期/中期/长期）
- 关键提醒

### 代码解释功能

#### 3. `explaining-code` Skill - 代码解释

通过可视化图表和类比来解释代码，帮助理解代码逻辑和工作原理。

**解释方式**：
1. **类比法**: 将代码与日常生活中的事物进行比较
2. **图表展示**: 使用 ASCII 艺术展示流程、结构或关系
3. **逐步讲解**: 一步一步地解释代码执行过程
4. **易错点提示**: 标注常见的错误或误解

### 数据流分析功能 ✨ 新增

#### 4. `/analyze-data` 命令 - 快速数据流分析

自动分析当前 git 修改中的数据流动，识别新增或修改的数据，追踪其来源、计算和用途。

**适用场景**：
- 快速了解当前修改涉及的数据流
- 检查修改是否引入了数据流变化
- 理解新增代码的数据处理逻辑

#### 5. `/trace-data-source` 命令 - 追踪数据来源

深入追踪指定变量或数据的完整来源链路。

**适用场景**：
- 调试时需要知道变量从哪里来
- 理解方法参数的原始数据源
- 追踪数据库查询结果的使用路径

**用法示例**：
```bash
/trace-data-source userName
/trace-data-source finalAmount
/trace-data-source ContractService.java:45
```

#### 6. `/analyze-calculation` 命令 - 分析计算过程

详细分析数据的计算和转换逻辑，解释计算公式和中间步骤。

**适用场景**：
- 理解复杂的计算逻辑
- 验证计算公式是否正确
- 学习 Stream API 的数据转换过程

**用法示例**：
```bash
/analyze-calculation finalPrice
/analyze-calculation totalAmount
/analyze-calculation calculateDiscount
```

#### 7. `/explain-data-flow` 命令 - 解释完整数据流

全面分析一段代码中的完整数据流动，包括所有数据的来源、转换和用途。

**适用场景**：
- 理解整个方法的数据处理过程
- 代码审查时了解数据流设计
- 学习他人代码的数据处理逻辑

**用法示例**：
```bash
/explain-data-flow OrderService.java
/explain-data-flow processOrder
/explain-data-flow
```

#### 8. `data-flow-tracing` Skill - 数据流追踪方法论

提供数据流分析的专业方法论，Claude 会在分析数据流时自动使用此技能。

**核心能力**：
- 识别数据来源（参数、数据库、API、计算等）
- 分析数据转换（类型转换、映射、过滤、聚合等）
- 追踪数据路径（跨方法、跨文件、跨系统）
- 生成可视化数据流图

#### 9. `data-flow-tracer` Agent - 数据流追踪助手

专门处理数据流分析任务的自动化 Agent，当你询问数据相关问题时会自动触发。

**自动触发场景**：
- "这个变量从哪来？"
- "如何计算这个值？"
- "数据是怎么流动的？"
- "为什么这里是 null？"

## 安装使用

### 安装插件

```bash
# 克隆插件到本地
cd /path/to/your/plugins
git clone <repository-url>

# 或者将插件目录复制到 Claude Code 插件目录
```

### 使用方法

#### 代码审查命令

```bash
# 审查指定文件
/code-review src/service/ContractService.java

# 审查多个文件
/code-review src/service/*.java

# 审查代码片段（在对话中粘贴代码后）
/code-review
```

#### 数据流分析命令

```bash
# 分析当前修改的数据流
/analyze-data

# 追踪特定变量的来源
/trace-data-source userName
/trace-data-source finalAmount

# 分析计算过程
/analyze-calculation totalPrice
/analyze-calculation users.stream().map(...).collect(...)

# 解释方法的完整数据流
/explain-data-flow OrderService.java
/explain-data-flow processOrder
```

#### Skills 自动触发

在对话中，Claude Code 会根据上下文自动调用相应的 skill：

- 进行签约项目代码审查时 → 自动使用 `contract-cr` skill
- 需要解释代码时 → 自动使用 `explaining-code` skill
- 询问数据来源、计算或流动时 → 自动使用 `data-flow-tracing` skill

你也可以明确要求：

```
请使用 contract-cr 规范审查这段代码
请用图表解释这个函数的工作原理
请追踪 finalAmount 的数据来源
```

#### Agent 自动触发

当你询问数据相关问题时，`data-flow-tracer` agent 会自动处理：

```
这个 finalAmount 从哪来的？
如何计算 totalPrice 的？
解释一下 processOrder 方法的数据流动
为什么 contractReq.getPromiseInfo() 返回 null？
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
contract-dev-plugin/
├── .claude-plugin/
│   └── plugin.json              # 插件配置文件
├── commands/
│   ├── code-review.md           # 代码审查命令
│   ├── analyze-data.md          # 快速数据流分析命令
│   ├── trace-data-source.md     # 追踪数据来源命令
│   ├── analyze-calculation.md   # 分析计算过程命令
│   └── explain-data-flow.md     # 解释完整数据流命令
├── skills/
│   ├── code-review/             # 代码审查规范 skill
│   │   └── SKILL.md
│   ├── explaining-code/         # 代码解释 skill
│   │   └── SKILL.md
│   └── data-flow-tracing/       # 数据流追踪方法论 skill
│       └── SKILL.md
├── agents/
│   └── data-flow-tracer.md      # 数据流追踪助手 agent
└── README.md                    # 本文档
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

- **v2.0.0** (2026-01-29)
  - 新增数据流分析功能
  - 新增 4 个数据流分析命令：`analyze-data`, `trace-data-source`, `analyze-calculation`, `explain-data-flow`
  - 新增 `data-flow-tracing` skill 和 `data-flow-tracer` agent
  - 增强插件能力：从代码审查扩展到数据流分析

- **v1.0.0** (2026-01-17)
  - 初始版本发布
  - 支持 `/code-review` 命令
  - 包含 `contract-cr` 和 `explaining-code` skills

## 作者

**11来了**

## 许可证

MIT License

## 反馈与支持

如有问题或建议，请提交 Issue 或 Pull Request。
