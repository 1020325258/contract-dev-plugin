---
description: 将开发经验持久化为 skill 文档，采用分层索引结构，支持渐进式披露。
argument-hint: "[指定要写入的内容]"
allowed-tools: Read, Write, Edit, Grep, Glob
---

## 职责
按照**分层知识架构**，将开发经验写入对应位置，确保：
1. 顶层 `SKILL.md` 仅作为**导航索引**，不嵌入完整内容
2. 具体知识按主题分目录存放在 `references/` 下
3. 通过渐进式披露避免 agent 被海量上下文淹没

## 插件源码目录
`/Users/zqy/work/AI-Project/claude-code-plugins/sales-project-plugins/contract-dev-plugin/`

---

## 知识分层架构

```
skills/<skill-name>/
├── SKILL.md                    # 顶层索引（仅导航，不嵌入内容）
└── references/
    ├── _overview.md            # 知识地图概览（可选）
    ├── domain/                 # 业务领域知识
    │   ├── quotation.md        # 报价单相关
    │   ├── contract.md         # 合同相关
    │   └── suborder.md         # S单/子订单相关
    ├── technical/              # 技术实现规范
    │   ├── rpc.md              # RPC调用规范
    │   ├── s3-upload.md        # 文件上传规范
    │   └── pdf-generation.md   # PDF生成规范
    ├── workflow/               # 开发工作流经验
    │   ├── testing.md          # 测试相关经验
    │   └── troubleshooting.md  # 问题排查经验
    └── infrastructure/         # 基础设施配置
        ├── database.md         # 数据库表结构
        └── maven.md            # Maven配置问题
```

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

### 步骤 1：确定知识分类与目标目录

根据内容特征，选择 `references/` 下的子目录：

| 分类 | 判断依据 | 目标目录 |
|-----|---------|---------|
| **domain** | 业务流程、领域概念、业务规则 | `references/domain/` |
| **technical** | 技术实现、组件使用、API调用 | `references/technical/` |
| **workflow** | 开发流程、问题排查、最佳实践 | `references/workflow/` |
| **infrastructure** | 数据库、配置、环境相关 | `references/infrastructure/` |

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
在 `SKILL.md` 对应分类下添加导航条目：

```markdown
### [分类名称]
- [主题标题](./references/<子目录>/<文件名>.md) - 一句话描述
```

**索引条目要求**：
- 标题清晰，能准确反映内容主题
- 描述简洁，一句话说明"何时需要查阅此文档"
- 按重要性/使用频率排序

### 步骤 5：同步更新 plugin.json 版本

- 路径：`.claude-plugin/plugin.json`
- 对 `version` 字段做 patch 版本升级（如 `1.5.0` → `1.5.1`）

---

## 写入格式

### 知识文件模板

```markdown
# [主题标题]

## 概述
<!-- 一句话说明本文档解决的问题 -->

## 业务背景 / 技术背景
<!-- 必要的上下文信息 -->

## 核心流程 / 使用方式
<!-- 具体实现步骤 -->

## 注意事项
<!-- 易错点、边界条件 -->

## 相关链接
<!-- 关联的其他知识文档 -->
```

### 索引条目模板（SKILL.md 中）

```markdown
- [标题](./references/<目录>/<文件>.md) - 简要描述
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

- `业务背景` 没有十足把握不要修改
- 强制阅读相关领域知识文档，保证术语对齐
- 解释枚举含义时，务必读取枚举类源码，不能凭命名推测

---

## 示例

### 知识文件示例（references/domain/quotation-split.md）

```markdown
# 基础报价单拆分为协同报价单

## 概述
基础报价单拆分后，销售合同需从绑定基础报价单改为绑定协同报价单（换绑）。

## 业务背景
基础报价单内包含定软电品，发起正签时销售合同绑定基础报价单号；
正式套餐合同签署后，基础报价单拆分为多个协同报价单，
需将销售合同与拆分后的协同报价单关联。

## 核心流程

### 1. 监听拆分事件
- 事件类型：`BUDGET_BILL_SPLIT`
- 监听器：`BudgetBillSplitHandler`
- 参数：`originalBillCode`、`billCodeList`、`projectOrderId`

### 2. 获取个性化报价数据
```java
homeOrderDataConversionService.contractPersonalData(projectOrderId, billCodeList, null);
```

### 3. 换绑合同与报价单关系
- 绑定：`QuotationRelationCommonService#bindBillCodeRelationAfter`
- 解绑：`QuotationRelationCommonService#cancelRelationByBillCodeAndContractCode`

## 注意事项
- 换绑目的：防止同一协同报价单重复发起多个销售合同
```

### 索引条目示例（SKILL.md 中）

```markdown
### 业务领域
- [报价单拆分换绑](./references/domain/quotation-split.md) - 基础报价单拆分后销售合同的换绑流程
```

---

## 迁移指南

对于现有 skill 目录，执行以下迁移：

1. **识别 SKILL.md 中嵌入的完整内容**
2. **抽取为独立的 references 文件**
3. **按分类放入对应子目录**
4. **在 SKILL.md 中替换为索引链接**

迁移后，SKILL.md 应呈现清晰的**目录结构**，而非知识全文。
