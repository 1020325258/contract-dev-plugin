---
name: base-domain-knowledge
description: 签约领域基础
---

## 销售合同领域概念
**1. 销售合同报价信息获取**
代码导航：HomeOrderDataConversionService#contractPersonalData
方法职责：基于主单号+报价单号+变更单号查询个性化报价数据。
入参说明：
- `homeOrderNo`： 主单号。
- `billCodeList`：报价单号。
- `changeOrderId`：变更单号。
响应结果说明：
- `ContractSourceDataBO`：主订单封装的报价信息。
- `ContractSourceDataBO # personalContractDataList`： 销售合同发起时要用到的个性化报价部分信息。

