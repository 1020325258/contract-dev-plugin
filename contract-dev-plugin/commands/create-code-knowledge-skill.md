---
description: 按照规范进行创建，辅助创建签约领域知识的 skill 文档。
argument-hint: "[指定要写入的 skill 文档] [指定要写入的内容]"
allowed-tools: Read, Write, Edit, Grep, Glob
---

## 职责
按照规范进行创建，辅助创建签约领域知识的 skill 文档。

## 执行流程
**1. 找到要写入的 skill 文件**
如果用户提供了 skill 文档的路径，则在该 skill 文档中写入。
**2. 写入规范**
- 写入位置：在写入之前，先找该文档内部是否已经存在相关的知识，如果存在则基于此进行完善，不要修改结构；如果不存在，则在该 skill 文档后边追加领域知识。
- 版本升级：在更新 skill 文件之后，在 plugin.json 中同步对 version 升级。
- 前置信息：
**3. 写入格式**
二级标题：业务动作
三级标题1：业务背景
三级标题2：触发时机
三级标题3：核心流程
**4. 写入要求**
- **简洁性（核心原则）**：遵循**奥卡姆剃刀原则**，保持极致简洁。
  - ✅ **只写 Claude Code 无法通过工具推断的特定领域知识**
  - ❌ **禁止写入以下内容**：
    - Service/Repository 方法列表（Claude 可通过 Grep/Read 发现）
    - 标准 CRUD 方法说明（命名已足够清晰）
    - 代码实现细节（Claude 会自己读代码）
    - 可以从代码结构推断的信息
  - **判断标准**：如果 Claude 通过搜索代码、读取类定义、查看方法签名就能理解，就不要写入文档
- **必要性测试**：
  - 问自己：如果不添加这个内容，Claude 是否会误解业务逻辑？
  - 如果答案是"不会"或"可能不会"，就不要添加
- **准确性**：
    - `业务背景`部分如果你没有十足的把握，不要进行修改。
    - 为了保证写入内容的术语与签约领域内对齐，强制阅读 `/skills/read/references` 下的领域知识文档。
    - 枚举：在解释枚举对应含义时，务必读取枚举类，保证含义解释正确。
## 示例
```markdown
## 基础报价单拆分为多个协同报价单
### 业务背景
基础报价单内包含了定软电品，当发起正签与销售合同时，此时基础报价单未拆分为多个协同报价单，此时销售合同绑定的报价单号是基础报价单号；当正式套餐合同签署完成之后，基础报价单内的【非门窗暖部分】会拆分为多个协同报价单，此时基于已绑定的基础报价单号，将销售合同与拆分后的协同报价单号进行关联，称为“换绑“；换绑的目的是单独发起销售合同时，会弹窗选择协同报价单号，此时需要将已经关联过销售合同的协同报价单给过滤掉，不能对同一个协同报价单重复发起多个销售合同。
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


