---
name: base-domain-knowledge
description: 签约领域基础业务知识，进行任何动作之前，必须阅读当前文档
---

## 报价单领域概念

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

## 合同核心模型

### Contract（合同主表）
**模型位置**：`utopia-nrs-sales-project-dao/src/main/java/com/ke/utopia/nrs/salesproject/dao/model/contract/Contract.java`

**核心字段说明**：
- `contractCode`：合同唯一编号（业务主键）
- `contractNo`：合同编号（展示用）
- `projectOrderId`：业务主键（项目订单号）
- `changeOrderId`：变更单号（仅变更协议有值）
- `companyCode`：分公司编码
- `type`：合同类型（见 `ContractTypeEnum`）
  - `1` - 认购合同
  - `2` - 设计合同
  - `3` - 套餐正式合同
  - `4` - 套餐变更协议
  - `8` - 销售合同（个性化主材合同）
  - 更多类型参见 `ContractTypeEnum`
- `status`：合同状态（见 `ContractStatusEnum`）
  - `1` - 起草中
  - `2` - 待确认
  - `3` - 已确认
  - `4` - 待签署
  - `5` - 待提交审核
  - `6` - 审核中
  - `7` - 待盖公司章
  - `8` - 已签署
  - `9` - 已取消
  - `10` - 已驳回
  - `11` - 待盖第三方章
- `amount`：合同金额
- `relateContractCode`：关联合同编号（如授权协议关联主合同）
- `platformInstanceId`：协议平台实例 ID
- `previewKey`：预览文件 key
- `userSignedKey`：用户签署后文件 key
- `bothSignedKey`：双方签署后文件 key
- `thirdSignedKey`：三方签署后文件 key（存管协议等）
- `errorMessage`：合同发起失败信息

**常用 Service 方法**（`ContractService`）：
- `getByContractCode(String contractCode)`：根据合同编号获取合同
- `getContractInfo(String projectOrderId, Byte contractType)`：获取项目单下指定类型的合同
- `getContractList(String projectOrderId, Byte contractType)`：获取项目单下指定类型的所有合同
- `getLatestContract(String projectOrderId, Byte contractType)`：获取项目单下指定类型的最新合同
- `updateContractStatus(String contractCode, Integer updateStatus)`：更新合同状态
- `deleteSoftByContractCode(String contractCode)`：软删除合同

### ContractNode（合同节点表）
**模型位置**：`utopia-nrs-sales-project-dao/src/main/java/com/ke/utopia/nrs/salesproject/dao/model/contract/ContractNode.java`

**业务背景**：
合同在流转过程中会经历多个关键节点（创建、发起、审核、签署、盖章、完成等），`ContractNode` 用于记录这些关键节点的发生时间，用于合同时间轴展示和业务判断。

**核心字段说明**：
- `contractCode`：关联的合同编号
- `nodeType`：节点类型（见 `NodeTypeEnum`）
  - `1` - 创建时间
  - `2` - 发起合同时间
  - `3` - 最新提交审核时间
  - `4` - 最新审核通过时间
  - `5` - 用户确认时间
  - `6` - 申请用章时间
  - `7` - 用户签署完成时间
  - `8` - 盖公司章时间
  - `9` - 最终完成时间
  - `10` - 作废时间
  - `11` - 最新审核驳回时间
  - `13` - 合同已取消时间
  - `15` - 授权时间
- `fireTime`：节点发生时间（时间戳）

**重要特性**：
- **节点唯一性约束**：同一个合同（`contractCode`）的每种节点类型（`nodeType`）只会存在一条记录。如果对已存在的节点类型执行创建操作，会更新该节点的 `fireTime`，而不是新增记录。
- **时间差计算场景**：经常有导数需求需要计算同一合同不同节点之间的时间差（如：用户确认到签署完成的耗时），可以通过查询对应节点的 `fireTime` 进行计算。例如：
  - 合同发起到用户签署的时长：`nodeType=7的fireTime - nodeType=2的fireTime`
  - 审核通过到盖章完成的时长：`nodeType=8的fireTime - nodeType=4的fireTime`

**常用 Service 方法**（`ContractNodeService`）：
- `getListByContractCode(String contractCode)`：获取合同的所有节点
- `getListByContractCodesAndType(List<String> contractCodes, List<Byte> nodeTypeList)`：批量获取指定类型的节点
- `create(String contractCode, Byte nodeType)`：创建节点（使用当前时间）
- `updateOrCreate(String contractCode, Byte nodeType)`：更新或创建节点（幂等操作）
- `getByContractCodeAndType(String contractCode, Byte nodeType)`：获取合同的指定类型节点
- `softDeleteByContractCode(String contractCode)`：软删除合同的所有节点

