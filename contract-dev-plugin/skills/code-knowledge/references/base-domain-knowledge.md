---
name: base-domain-knowledge
description: 签约领域基础业务知识，进行任何动作之前，必须阅读当前文档
---

## 报价单领域术语

### 正签报价单与协同报价单
- **正签报价单**：报价领域的基础报价单概念，在正式套餐合同签署前使用。
- **协同报价单**：报价领域概念，来源有两种：
  - 基础报价单拆分：正式套餐合同签署完成后，基础报价单内的【非门窗暖部分】会拆分为多个协同报价单
  - 单独创建：可直接创建协同报价单

**关键特性**：
- 单个协同报价单内部可以选择套餐和商品，这些套餐和商品所属的主体不同，因此**单个协同报价单可能对应多个公司主体**（`companyCode`）
- 一个 `billCode` 可能对应多个 `companyCode`

## 销售合同领域概念
**1. 销售合同个性化报价数据获取**
代码导航：HomeOrderDataConversionService#contractPersonalData
方法职责：基于主单号+报价单号+变更单号查询个性化报价数据。
入参说明：
- `homeOrderNo`： 主单号。
- `billCodeList`：报价单号。
- `changeOrderId`：变更单号。
响应结果说明：
- `ContractSourceDataBO`：主订单封装的报价数据实体。
- `ContractSourceDataBO # personalContractDataList`： 销售合同发起时要用到的个性化报价数据。

