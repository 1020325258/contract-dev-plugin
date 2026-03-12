# 变更单取消时的合同处理

## 变更单取消时的合同处理

### 业务背景
变更单取消（`ChangeOperateEnum.CANCEL_CHANGE`）时，签约系统需要取消与该变更单关联的两类合同：
1. **B 变更协议**（正签变更类合同）
2. **C 销售合同**（新建的待签约个性化合同）

与**变更单撤销/审核驳回**（`ChangeOperateEnum.needRevertContract()`）不同：
- 取消（CANCEL_CHANGE）：直接将合同状态置为 `CANCEL`
- 撤销/驳回（needRevertContract）：将合同状态回退为草稿（undo）

### 触发时机
监听来自 `utopia-athena` 的变更单操作事件：
- `bizType`：`"utopia-atom-project-change"`（常量 `EventType.PROJECT_CHANGE_EVENT`）
- `serverName`：`"utopia-athena"`
- Payload 类型：`DomainEventDTO<KafkaMessageAtomProjectChangeEventDTO>`

**关键字段**：
- `payload.getProjectChangeNo()` → 变更单号
- `payload.getProjectOrderId()` → 原始项目单号（需通过 `commonBusinessService.getCoordinationProjectOrder` 换取整装项目单号）
- `payloadData.getPayloadData().getOperatorUcid()` → 操作人 ucid
- `payload.getOperateType()` → 操作类型，与 `ChangeOperateEnum` 枚举比对

### 核心流程

**处理器**：`ChangeOrderPayHandler`（`service/fund/handler/`），在 `handleBiz` 中对多个 operateType 分支处理，CANCEL_CHANGE 分支位于第 121 行。

1. 取消 B 变更协议：通过 `projectOrderId + changeOrderId` 查询变更合同，直接置为 CANCEL 并取消关联关系
2. 取消 C 销售合同：通过 `changeOrderId + ContractTypeEnum.PERSONAL` 查询待签约的个性化合同，直接置为 CANCEL 并取消关联关系
