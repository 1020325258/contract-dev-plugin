---
description: 按照规范进行创建，辅助创建签约领域知识的 skill 文档。
argument-hint: "[指定要写入的内容]"
allowed-tools: Read, Write, Edit, Grep, Glob
---

## 职责
按照规范，将用户提供的签约领域开发经验写入 `/Users/zqy/work/AI-Project/claude-code-plugins/sales-project-plugins/contract-dev-plugin/skills/code-developer` 目录下的开发技能文档。

## 执行流程

**1. 在 references 中检索是否已有类似经验**
- 扫描 `skills/code-developer/references/` 目录下所有 `.md` 文件
- 逐一判断各文件主题是否与本次经验相关
- **命中**（已有相关内容）→ 进入步骤 2
- **未命中**（无相关内容）→ 进入步骤 3

**2. 已有相关内容：定位并修改**
- 找到相关段落，在原有位置进行补充或完善
- 不改变文件整体结构，不修改其他无关内容
- 完成后跳至步骤 4

**3. 无相关内容：判断写入位置**
- **可归入某个现有 references 文件的主题**（如属于 RPC 调用、定时任务等）→ 追加到该文件末尾
- **属于全新主题**（现有文件均不适合）→ 在 `references/` 下新建一个语义明确的 `.md` 文件，并在 `SKILL.md` 的"领域开发经验"部分添加对应入口
- 完成后进入步骤 4

**4. 同步更新 plugin.json 版本**
- 路径：`/Users/zqy/work/AI-Project/claude-code-plugins/sales-project-plugins/contract-dev-plugin/.claude-plugin/plugin.json`
- 对 `version` 字段做 patch 版本升级（如 `1.4.1` → `1.4.2`）

---

## 写入格式
```markdown
## <业务动作>
### 业务背景
### 触发时机
### 核心流程
```

---

## 写入要求

**简洁性（核心原则）**：遵循奥卡姆剃刀原则，保持极致简洁。
- ✅ 只写 Claude Code 无法通过工具推断的特定领域知识
- ❌ 禁止写入：Service/Repository 方法列表、标准 CRUD 说明、可从代码结构直接推断的信息
- **判断标准**：如果 Claude 搜代码就能理解，就不要写

**必要性测试**：
- 如果不添加这个内容，Claude 是否会误解业务逻辑？
- 答案是"不会"或"可能不会"→ 不写

**准确性**：
- `业务背景` 没有十足把握不要修改
- 强制阅读 `skills/code-reader/references/` 下的领域知识文档，保证术语与签约领域对齐
- 解释枚举含义时，务必读取枚举类源码，不能凭命名推测

---

## 示例

```markdown
## 基础报价单拆分为多个协同报价单
### 业务背景
基础报价单内包含了定软电品，当发起正签与销售合同时，此时基础报价单未拆分为多个协同报价单，此时销售合同绑定的报价单号是基础报价单号；当正式套餐合同签署完成之后，基础报价单内的【非门窗暖部分】会拆分为多个协同报价单，此时基于已绑定的基础报价单号，将销售合同与拆分后的协同报价单号进行关联，称为"换绑"；换绑的目的是单独发起销售合同时，会弹窗选择协同报价单号，此时需要将已经关联过销售合同的协同报价单给过滤掉，不能对同一个协同报价单重复发起多个销售合同。
### 触发时机
正式套餐合同签署完成后。

### 核心流程说明
**1. 监听报价领域的基础报价单拆分事件**
事件类型：`BUDGET_BILL_SPLIT`（来自 utopia-athena）。
参数说明：
- `originalBillCode`：原基础报价单编号。
- `billCodeList`：拆分后的协同报价单编号列表。
- `projectOrderId`：项目订单号。
监听器：`BudgetBillSplitHandler`。

**2. 获取个性化报价数据**
方法：`homeOrderDataConversionService.contractPersonalData(projectOrderId, billCodeList, null)`。

**3. 绑定合同与报价单的关系**
方法：`QuotationRelationCommonService#bindBillCodeRelationAfter`
职责：将合同与拆分后的协同报价单进行绑定。

**4. 解绑合同与基础报价单的关系**
方法：`QuotationRelationCommonService#cancelRelationByBillCodeAndContractCode`
```
