---
description: 将开发经验持久化为 skill 文档，采用三层知识架构，让 agent 更容易理解和发现知识。
argument-hint: "[指定要写入的内容]"
allowed-tools: Read, Write, Edit, Grep, Glob
---

## 职责
按照**三层知识架构**，将开发经验写入对应位置，确保：
1. 顶层 `SKILL.md` 仅作为**导航索引**，不嵌入完整内容
2. 具体知识按层级分目录存放在 `references/` 下
3. 三层结构帮助 agent 快速判断知识的重要性和用途

## 插件源码目录
`/Users/zqy/work/AI-Project/claude-code-plugins/sales-project-plugins/contract-dev-plugin/`

---

## 三层知识架构

```
skills/<skill-name>/
├── SKILL.md                      # 顶层索引（仅导航，不嵌入内容）
└── references/
    ├── foundation/               # 基础层：每次开发必须具备的知识
    │   ├── domain-concepts.md    # 核心领域概念、术语定义
    │   └── database-schema.md   # 数据库表结构 DDL
    ├── domain/                   # 业务领域层：特定功能开发时需要的知识
    │   ├── contract-flow.md      # 合同流程规则
    │   └── apollo-switches.md   # Apollo 开关配置
    └── experience/               # 实践经验层：踩坑记录、反直觉的配置陷阱
        ├── kafka-pitfalls.md     # Kafka 配置导致服务无法启动
        └── bpm-approval.md      # BPM 审批加签配置
```

### 各层定义

| 层级 | 目录 | 内容定性 | 判断标准 |
|------|------|---------|---------|
| **基础层** | `references/foundation/` | DDL、核心领域概念、基础配置 | 缺少这些知识，开发会产生根本性误解 |
| **业务领域层** | `references/domain/` | Apollo 开关、业务流程规则、领域逻辑 | 特定功能开发才需要，不是每次都用 |
| **实践经验层** | `references/experience/` | 踩坑记录、反直觉配置、环境问题 | 仅靠读代码无法发现，需要亲历才知道 |

---

## 执行流程

### 步骤 0：判断知识类型，选择目标 skill

| 知识类型 | 关键词示例 | 目标 skill |
|---------|-----------|-----------|
| 签约业务知识 | 报价单、合同、S单、变更单、签约、billCode | `skills/code-developer` |
| Spring AI Alibaba | Agent、Graph、StateGraph、编排、checkpoint | `skills/spring-ai-alibaba-developer` |
| TDD/测试规范 | 单元测试、Mock、集成测试、测试驱动 | `skills/test-driven-development` |
| 项目结构 | DDD、包结构、分层、模块划分 | `skills/project-structure` |
| 代码审查 | 空指针、Optional、代码规范、CR | `skills/code-review` |

**判断规则**：
1. 优先匹配关键词，命中则写入对应 skill
2. 多个关键词命中时，选择匹配度最高的
3. 无匹配时默认写入 `skills/code-developer`

### 步骤 1：确定知识层级与目标目录

根据内容特征，选择对应层级：

| 内容特征 | 层级 | 目标目录 |
|---------|------|---------|
| 数据库 DDL、表结构、字段含义 | 基础层 | `references/foundation/` |
| 核心领域概念、必知术语定义 | 基础层 | `references/foundation/` |
| Apollo 开关配置、Feature Flag | 业务领域层 | `references/domain/` |
| 业务流程规则、领域逻辑 | 业务领域层 | `references/domain/` |
| Kafka/MQ 配置陷阱 | 实践经验层 | `references/experience/` |
| BPM 审批流程配置 | 实践经验层 | `references/experience/` |
| 环境问题、启动失败排查 | 实践经验层 | `references/experience/` |
| Maven/测试工具问题 | 实践经验层 | `references/experience/` |

**边界判断**：
- 有业务规则但同时是基础概念 → 优先归入基础层
- 技术实现规范（RPC、分布式锁）→ 判断是否每次开发都需要：是 → 基础层；否 → 业务领域层

### 步骤 2：检索是否已有相关内容

- 扫描目标子目录下所有 `.md` 文件
- 判断文件主题是否与本次经验相关
- **命中** → 进入步骤 3（修改现有文件）
- **未命中** → 进入步骤 4（新建文件）

### 步骤 3：已有相关内容 — 定位修改

- 找到相关段落，在原有位置补充或完善
- **不改变文件整体结构**
- 完成后跳至步骤 5

### 步骤 4：无相关内容 — 新建文件并更新索引

**4.1 创建知识文件**
- 在目标子目录下新建语义明确的 `.md` 文件
- 文件命名规则：`<主题关键词>.md`（小写，连字符分隔）

**4.2 更新 SKILL.md 索引**
在 `SKILL.md` 对应层级分组下添加导航条目：

```markdown
### [基础层] 必读
- [主题标题](./references/foundation/<文件名>.md) - 一句话描述

### [业务领域层] 按需查阅
- [主题标题](./references/domain/<文件名>.md) - 一句话描述

### [实践经验层] 遇到问题时查阅
- [主题标题](./references/experience/<文件名>.md) - 一句话描述
```

**索引条目要求**：
- 标题清晰，能准确反映内容主题
- 描述简洁，一句话说明"何时需要查阅此文档"
- 基础层条目排在最前，实践经验层排在最后

### 步骤 5：同步更新 plugin.json 版本

- 路径：`.claude-plugin/plugin.json`
- 对 `version` 字段做 patch 版本升级（如 `1.8.5` → `1.8.6`）

---

## 写入格式

### 知识文件模板

```markdown
# [主题标题]

## 概述
<!-- 一句话说明本文档解决的问题 -->

## 背景
<!-- 必要的上下文信息 -->

## 核心内容
<!-- 具体内容：DDL / 配置项 / 业务规则 / 踩坑过程 -->

## 注意事项
<!-- 易错点、边界条件 -->

## 相关链接
<!-- 关联的其他知识文档 -->
```

### 索引条目模板（SKILL.md 中）

```markdown
- [标题](./references/<层级目录>/<文件>.md) - 简要描述
```

---

## 写入原则

### 渐进式披露原则

**SKILL.md 只做导航，不嵌入完整内容**：
- ✅ 正确：在 SKILL.md 中放索引链接 + 一句话描述
- ❌ 错误：在 SKILL.md 中直接写完整流程

**判断标准**：
- 如果内容超过 3 行，就应该放入 references 文件
- SKILL.md 的单个条目描述不超过 1 行

### 简洁性原则

遵循奥卡姆剃刀原则：
- ✅ 只写 Claude Code 无法通过工具推断的特定领域知识
- ❌ 禁止写入：Service/Repository 方法列表、标准 CRUD 说明、可从代码结构直接推断的信息

**必要性测试**：
- 如果不添加这个内容，Claude 是否会误解业务逻辑？
- 答案是"不会"或"可能不会" → 不写

### 准确性原则

- `背景` 没有十足把握不要修改
- 强制阅读相关领域知识文档，保证术语对齐
- 解释枚举含义时，务必读取枚举类源码，不能凭命名推测

---

## 示例

### 实践经验层文件示例（references/experience/bpm-approval.md）

```markdown
# BPM 审批加签配置

## 概述
BPM 流程中加签功能需要额外配置，否则审批节点无法正常展示加签入口。

## 背景
项目使用内部 BPM 系统处理合同审批流程，加签（在审批过程中临时增加审批人）
需要在流程定义中显式开启，默认不可用。

## 核心内容
在流程定义 XML 中，目标审批节点需添加：
```xml
<extensionElements>
  <activiti:taskListener event="create" class="...AddSignListener"/>
</extensionElements>
```

同时 Apollo 中需配置：`bpm.add-sign.enabled=true`

## 注意事项
- 旧版流程定义升级时，该配置不会自动继承，需手动补充
- 测试环境和生产环境的 Apollo 配置独立，上线前需同步
```

### 业务领域层文件示例（references/domain/apollo-switches.md）

```markdown
# Apollo 开关配置

## 概述
签约系统中影响核心流程的 Apollo 开关汇总。

## 开关列表

| 开关 Key | 默认值 | 作用 |
|---------|--------|------|
| `contract.sign.auto-confirm` | false | 是否自动确认签约 |
| `contract.pdf.async-generate` | true | PDF 是否异步生成 |
```

### 索引条目示例（SKILL.md 中）

```markdown
### [基础层] 必读
- [核心领域概念](./references/foundation/domain-concepts.md) - 报价单、合同、S单等核心术语定义

### [业务领域层] 按需查阅
- [Apollo 开关配置](./references/domain/apollo-switches.md) - 影响签约流程的 Apollo 配置项

### [实践经验层] 遇到问题时查阅
- [BPM 审批加签配置](./references/experience/bpm-approval.md) - 加签功能未生效的排查与配置
```

---

## 迁移指南

对于使用旧版四目录结构（domain/technical/workflow/infrastructure）的 skill，执行以下迁移：

| 旧目录 | 内容特征 | 迁移到 |
|--------|---------|--------|
| `infrastructure/` | DDL、数据库表结构 | `foundation/` |
| `domain/` 中的核心概念文件 | 基础领域术语、必知业务模型 | `foundation/` |
| `domain/` 中的流程规则文件 | 具体业务流程、Apollo配置 | `domain/` |
| `technical/` | 技术规范（RPC/锁/上传等） | 按使用频率：高频 → `foundation/`，低频 → `domain/` |
| `workflow/` | 踩坑、排查问题、测试工具经验 | `experience/` |

迁移步骤：
1. 在目标层级目录下新建文件（或直接移动文件）
2. 更新 SKILL.md 中的索引链接路径
3. 删除旧目录下的空目录
