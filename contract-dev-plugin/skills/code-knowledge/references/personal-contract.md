---
name: personal-contract
description: 记录签约领域内部涉及的销售合同、报价单、报价领域交互逻辑。
---

## 基础报价单拆分为多个协同报价单
### 业务背景
基础报价单内包含了定软电品，当发起正签与销售合同时，此时基础报价单未拆分为多个协同报价单，此时销售合同绑定的报价单号是基础报价单号；当正式套餐合同签署完成之后，基础报价单内的【非门窗暖部分】会拆分为多个协同报价单，此时基于已绑定的基础报价单号，将销售合同与拆分后的协同报价单号进行关联，称为"换绑"；换绑的目的是单独发起销售合同时，会弹窗选择协同报价单号，此时需要将已经关联过销售合同的协同报价单给过滤掉，不能对同一个协同报价单重复发起多个销售合同。

### 触发时机
正式套餐合同签署完成后。

### 核心流程说明
处理类：`BudgetBillSplitHandlerV3#dealBudgetBillSplit`

**1. 获取正签合同**
通过 `projectOrderId` 获取最新的正式套餐合同（`ContractTypeEnum.PACKAGE_FORMAL`）。

**2. 获取关联的个性化合同**
通过正签合同获取与其合并发起的销售合同（个性化合同），筛选条件：
- 合同类型为 `ContractTypeEnum.PERSONAL`
- 合同状态在 `ContractStatusEnum.validStatusWithoutDraft` 范围内

**3. 按主体分组**
将个性化合同按 `companyCode`（主体）分组，便于后续匹配。

**4. 获取个性化报价数据**
方法：`homeOrderDataConversionService.contractPersonalData(projectOrderId, billCodeList, null)`
返回拆分后的协同报价单数据，包含报价单号和所属公司主体。

**5. 按公司主体匹配合同与报价单**
遍历个性化报价数据，按 `organizationCode`（公司主体）匹配对应的个性化合同：
- **绑定关系**：调用 `quotationRelationCommonService.bindBillCodeRelationAfter(contract, billCodes)` 将拆分后的协同报价单与合同绑定
- **解绑关系**：调用 `quotationRelationCommonService.cancelRelationByBillCodeAndContractCode(contractCode, originalBillCode)` 解除原基础报价单与合同的关系
