# 协同报价单/变更单撤回 - S 单撤回合同

## 业务背景
协同报价单/变更单撤回时，如果该报价单/变更单未直接关联合同，可能是由于已下单换成 S 单，合同已换绑到 S 单。此时需要通过 S 单来撤回对应合同。

**关键业务规则**：协同报价单/变更单与其对应的 S 单，任意时刻只有一种与合同绑定（要么报价单/变更单直接绑定，要么 S 单绑定）。

## 触发时机
监听 `utopia-athena` 领域事件。

### 协同报价单撤回
- 事件类型：`SIGN_COOPER_BUDGET_BILL`（协同报价单）或 `GROUP_BUDGET_BILL`（团装报价单）
- 状态变化：正式版(3) → 调整中(1)/已提交(2)，或 已提交(2) → 调整中(1)
- 监听器：`CancelPersonalContractListener`

### 变更单撤回
- 事件类型：`CHANGE_ORDER`（变更单）
- 监听器：`ChangeOrderRevocationListener`（需确认具体监听器名称）

## 核心流程

**1. 查询报价单/变更单是否关联合同**
- 方法：`QuotationRelationCommonService#getContractByBillCode`（协同报价单）
- 方法：`ContractQuotationRelationService#getByBillCodesAndStatus`（变更单，`BindTypeEnum.CHANGE_ORDER`）
- 已关联合同 → 直接处理绑定关系
- 未关联合同 → 进入 S 单撤回逻辑

**2. 查询报价单/变更单对应的 S 单**
- 方法：`SubOrderFeignService#queryValidBaseInfoByHomeOrderNo`
- 参数：`projectOrderId`、`billCode`（协同报价单）或 `changeOrderId`（变更单）

**3. 查询 S 单关联合同（bindType=SUB_ORDER）**
- 方法：`ContractQuotationRelationService#getByBillCodesAndStatus`
- 参数：`subOrderNos`、`RelationStatusEnum.RELATED`、`BindTypeEnum.SUB_ORDER`

**4. 对每个关联合同执行处理**

**4.1 合同状态校验**
以下情况跳过处理：
- 合同无效态（`ContractStatusEnum.CANCEL`）
- 合同终态（`ContractStatusEnum.SIGNED_STATUS_LIST`）
- 合同已确认后申请用章（`PENDING_USER_SIGN` + `userConfirmStatus=YES`）

**4.2 判断合同绑定情况**

| 合同绑定情况 | S 单对应情况 | 操作 |
|------------|------------|-----|
| 绑定了报价单或变更单 | - | 解除 S 单关联 + 撤回合同 |
| 仅绑定 S 单 | S 单完全一致 | 作废合同 |
| 仅绑定 S 单 | S 单不完全一致 | 解除当前 S 单关联 + 撤回合同 |

**关键判断逻辑**：
- 绑定报价单/变更单：`bindType = 1(BILL_CODE)` 或 `bindType = 2(CHANGE_ORDER)`
- S 单完全一致：合同绑定的 S 单集合 `equals` 当前协同报价单/变更单对应的 S 单集合

**4.3 执行解绑操作**
- 方法：`ContractQuotationRelationService#cancelRelationsByBillCodes`
- **重要**：同时尝试解绑报价单/变更单号 AND S 单号
- 原因：报价单/变更单可能已下单生成 S 单，但 S 单尚未完成与合同的绑定
- 该方法会自动处理不存在的绑定关系（无操作）

**5. 清理正签草稿字段**

### 协同报价单撤回
- 方法：`ContractFieldHandler#removeBillCodeFromContractField`（移除协同报价单号）
- 方法：`ContractFieldHandler#removeSubOrderNoFromContractField`（移除 S 单号）

### 变更单撤回
- 方法：`ContractFieldHandler#removeChangeOrderIdFromContractField`（移除变更单号）
- 方法：`ContractFieldHandler#removeSubOrderNoFromContractField`（移除 S 单号）

## 核心服务

### PersonalRelationHandler
处理合同与报价单/S单绑定关系的核心接口：
- `revokeCooperQuotation(projectOrderId, billCode, operatorUcid)`：撤回协同报价单
- `revokeChangeOrder(projectOrderId, changeOrderId, operatorUcid)`：撤回变更单

## 关键数据结构

### ContractQuotationRelation.bindType
| 值 | 枚举 | 说明 |
|---|-----|-----|
| 1 | BILL_CODE | 报价单号 |
| 2 | CHANGE_ORDER | 变更单号 |
| 3 | SUB_ORDER | 子单号（S 单） |
