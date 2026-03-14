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
处理类：`BudgetBillSplitHandlerV2#dealBudgetBillSplit`

**1. 获取正签合同**
通过 `projectOrderId` 获取最新的正式套餐合同（`ContractTypeEnum.PACKAGE_FORMAL`）。

**2. 获取正签合同关联发起的销售合同**
方法：`getRelatedPersonalContracts(formalContract)`
通过正签合同的合同编号获取关联关系（`contractRelationService.getRelationList`），再查询关联的销售合同，筛选条件：
- 合同类型为 `ContractTypeEnum.PERSONAL`
- 合同状态在 `ContractStatusEnum.validStatusWithoutDraft` 范围内（不包括草稿状态的有效状态）

**3. 按公司主体对销售合同分组**
将销售合同按 `companyCode`（公司主体）转换为 Map，key 为公司主体，value 为合同对象，便于后续按主体匹配。
变量名：`relatedPersonalContractByCompanyCode`

**4. 通过报价单号获取个性化报价数据**
方法：`homeOrderDataConversionService.contractPersonalData(projectOrderId, billCodeList, null)`
返回拆分后的协同报价单数据（`ContractSourceDataBO`），包含报价单号和所属公司主体（`organizationCode`）。

**5. 个性化报价数据按照公司主体分组**
将个性化报价数据按 `organizationCode`（公司主体）分组，便于后续按主体进行报价单的换绑操作。
变量名：`personalContractDataByCompanyCode`

**6. 按照主体分组，进行报价单的解绑与绑定**
遍历个性化报价数据分组，按 `organizationCode`（公司主体）匹配对应的销售合同：
- **绑定关系**：调用 `quotationRelationCommonService.bindBillCodeRelationAfter(personalContract, billCodes)` 将拆分后的协同报价单与合同绑定
- **解绑关系**：调用 `quotationRelationCommonService.cancelRelationByBillCodeAndContractCode(contractCode, originalBillCode)` 解除原基础报价单与合同的关系

## 个性化报价单撤回处理
### 业务背景
个性化报价单撤回时（报价单状态从"正式版"回退到"调整中"或"已提交"），需要同步处理关联的销售合同状态，包括解除合同与报价单的绑定关系、撤销合同或回退合同状态。

### 触发时机
监听报价领域的报价单状态变更事件，判断为撤回操作时触发：
- 状态变更：`3→1`（正式版→调整中）或 `3→2`（正式版→已提交）或 `2→1`（已提交→调整中）
- 报价单类型：协同报价单或集采报价单

### 核心流程说明
处理类：`CancelPersonalContractListener#handleBiz`

**1. 处理附件撤回**
方法：`homeOrderOperationService.revokeQuote(billCode, orderKind, projectOrderId)`

**2. 获取关联合同**
方法：`quotationRelationCommonService.getContractByBillCode(billCode)` 获取该报价单绑定的所有合同。

**3. 分场景处理**

**场景一：报价单已绑定合同**
- **唯一报价单场景**：合同仅绑定该报价单时，解除所有绑定关系并撤销合同
  - `quotationRelationCommonService.cancelRelationByBillCode(contractCode)` 解除关联
  - `commonContractService.cancelCurrentContract(contract, operatorUcid, true)` 撤销合同
- **多报价单场景**：合同绑定多个报价单时，仅解除该报价单绑定并回退合同状态到草稿
  - `quotationRelationCommonService.cancelRelationByBillCodeAndContractCode(contractCode, billCode)` 解除该报价单关联
  - `homeAndPcCommonService.undoContract(contract, operatorUcid)` 回退合同状态
- **清理正签合同数据**：从关联的正签合同的合同数据表（contract_field）中移除该报价单号
  - 从 `billCodeInfoList` 字段中移除
  - 从 `billCodeList` 字段中移除

**场景二：报价单未绑定合同（历史数据）**
通过 `projectOrderId` 获取订单下最新的个性化合同，筛选状态包括：起草中、待确认、待签署、待提交审核、审核中、待盖公司章。检查合同数据表中 `billCodeList` 字段是否包含该报价单号，如包含则直接撤销合同。
