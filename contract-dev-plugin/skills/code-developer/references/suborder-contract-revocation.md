# 协同报价单撤回 - S 单撤回合同

## 业务背景
协同报价单撤回时，如果该报价单未直接关联合同，可能是由于协同报价单已下单换成 S 单，合同已由协同报价单换绑到 S 单。此时需要通过 S 单来撤回对应合同。

## 触发时机
协同报价单/团装报价单撤回时，监听 `utopia-athena` 领域事件。
- 事件类型：`SIGN_COOPER_BUDGET_BILL`（协同报价单）或 `GROUP_BUDGET_BILL`（团装报价单）
- 状态变化：正式版(3) → 调整中(1)/已提交(2)，或 已提交(2) → 调整中(1)
- 监听器：`CancelPersonalContractListener`

## 核心流程

**1. 查询协同报价单是否关联合同**
- 方法：`QuotationRelationCommonService#getContractByBillCode`
- 已关联合同 → 按原有逻辑处理（直接撤回/作废合同）
- 未关联合同 → 进入 S 单撤回逻辑

**2. 查询协同报价单对应的 S 单**
- 方法：`SubOrderFeignService#queryValidBaseInfoByHomeOrderNo`
- 参数：`projectOrderId`、`billCode`

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
- S 单完全一致：合同绑定的 S 单集合 `equals` 当前协同报价单对应的 S 单集合

**5. 清理正签草稿字段**
- 方法：`ContractFieldHandler#removeBillCodeFromContractField`（移除协同报价单号）
- 方法：`ContractFieldHandler#removeSubOrderNoFromContractField`（移除 S 单号）

## 关键数据结构

### ContractQuotationRelation.bindType
| 值 | 枚举 | 说明 |
|---|-----|-----|
| 1 | BILL_CODE | 报价单号 |
| 2 | CHANGE_ORDER | 变更单号 |
| 3 | SUB_ORDER | 子单号（S 单） |
