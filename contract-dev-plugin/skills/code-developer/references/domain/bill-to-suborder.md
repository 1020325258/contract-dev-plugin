# 报价单/变更单下单后绑定 S 单

## 业务背景
报价单（或变更单）完成下单后，会产生 S 单（子单）。签约系统需要监听下单完成事件，将销售合同与对应的 S 单进行绑定，以便后续发起合同时能感知到 S 单的存在。

协同报价单/团装报价单在换绑时，**需要解绑原报价单关联，再绑定 S 单**；而正签基础报价单和变更单换绑时，**只新增 S 单绑定，不解绑原单据关联**，原因是基础报价单后续可能会拆分为多个协同报价单，需要保留基础报价单与合同的关联作为拆分依据；变更单同理，需保留变更单号以支持后续流程追溯。

## 触发时机
- 正签报价单下单完成后（`QUOTATION_CREATE_ORDER` 事件）
- 变更单下单完成后（`QUOTATION_CHANGE_CREATE_ORDER` 事件）

Kafka payload 中，变更单号字段为 `projectChangeNo`（非 `changeOrderNo`）。

## 核心流程

**1. 监听下单完成事件**
处理器位于 `service/contract/kafka/listener/personal/relation/` 包下：
- `BillToSubOrderListener`：处理报价单下单（`QUOTATION_CREATE_ORDER`），需先查询报价单类型以区分协同报价单、团装报价单、基础报价单，走不同的换绑逻辑。
- `ChangeBillToSubOrderListener`：处理变更单下单（`QUOTATION_CHANGE_CREATE_ORDER`）。

**2. 换绑目标合同范围**
换绑仅针对销售合同（`ContractTypeEnum.PERSONAL`），根据主单号查询所有有效态（不含草稿）的销售合同，逐个委托 `QuotationRelationCommonService` 处理换绑。

**3. 换绑行为差异**
- 协同/团装报价单：解绑报价单，绑定 S 单（`convertCooperBillToSubOrder`）
- 正签基础报价单：仅绑定 S 单，保留基础报价单关联（`convertStandardBillToSubOrder`）
- 变更单：仅绑定 S 单，保留变更单关联（`convertChangeToSubOrder`）

## 关键注意事项

### 关联关系中 S 单的三类来源

`contract_quotation_relation` 表中，`bind_type=3`（SUB_ORDER）的记录来源有三类：

| 来源 | 换绑行为 | 换绑后原单据是否保留 |
|-----|---------|----------------|
| 基础报价单（bind_type=1） | 绑定 S 单，**保留**基础报价单关联 | ✅ 保留 |
| 协同报价单（bind_type=1） | 绑定 S 单，**解绑**协同报价单关联 | ❌ 移除 |
| 变更单（bind_type=2） | 绑定 S 单，**保留**变更单关联 | ✅ 保留 |

> **注意**：协同报价单与基础报价单的 `bind_type` 相同，均为 `1`（BILL_CODE），区分二者需通过查询报价单系统获取报价单类型（`GeneralBillTypeEnum`）。

**检查绑定关系时的识别方式**：

对于合同下 `bind_type=3` 的 S 单，可通过以下方式判断其来源：
- 若能在 `bind_type=1` 记录中找到对应的基础报价单，则为**基础报价单 S 单**
- 若能在 `bind_type=2` 记录中找到对应的变更单，则为**变更单 S 单**
- 以上均未命中的 S 单，则为**协同报价单换绑留下的 S 单**，属正常业务现象，不应视为缺失或异常

### `SubOrderBaseInfoDTO` 的公司主体字段是 `getMdmCode()`

查询 S 单时，要过滤"主体与合同一致"的 S 单，使用的是 `SubOrderBaseInfoDTO::getMdmCode()`，**不是 `getCompanyCode()`**。

```java
subOrderFeignService.queryValidBaseInfoByHomeOrderNo(projectOrderId, billCode, null)
    .stream()
    .filter(dto -> contract.getCompanyCode().equals(dto.getMdmCode()))  // ✅
    .map(SubOrderBaseInfoDTO::getOrderNo)
    ...
```

### `ContractQuotationRelationService#getByContractCode` 默认只返回 BILL_CODE 类型

```java
// 默认 bindType = BILL_CODE(1)，只返回报价单关联
getByContractCode(contractCode, status)

// 传 null 才能获取所有 bindType（报价单、变更单、子单）
getByContractCode(contractCode, status, null)
```

需要查询全部类型时**必须显式传 `null`**，否则会漏掉变更单和子单的关联关系。

### 合同绑定关系校验（checkBindingByOrderId）

**接口位置**：`ContractToolService#checkBindingByOrderId`

**功能**：校验订单下销售合同的绑定关系是否正确

**校验维度**：
- 基础报价单 → S 单换绑校验（需先判断报价单类型，仅校验 `BUDGET_STANDARD` 类型）
- 变更单 → S 单换绑校验
- 协同报价单 → S 单换绑校验（需过滤无效状态：IN_ADJUST、DELETED、CANCELED）

**有效单据的获取逻辑**：
- **有效基础报价单**：从关联表拿到 status=1 的，且类型为基础报价单
- **有效协同报价单**：从关联表拿到 status=1 或 2 的，且状态有效（非 IN_ADJUST、DELETED、CANCELED），且类型为协同报价单（BUDGET_COOPER 或 BUDGET_GROUP）
- **有效变更单**：从关联表拿到 status=1 的，bind_type 为变更单类型

**漏换绑判断逻辑**：
- 先通过 `queryValidBaseInfoByHomeOrderNo` 获取该报价单对应的所有 S 单（主体与合同一致）
- 再判断这些 S 单是否都在当前合同上已绑定
- `missing = expectedSubOrders - boundSubOrderNos`
- **注意**：协同报价单的漏换绑判断逻辑与基础报价单/变更单一致，即如果该报价单对应的S单全部在当前合同上绑定了，那么就没有漏的

**协同报价单校验特殊性**：
- 查询关联关系时需要**分两次查询**：`status=1`（已关联）和 `status=2`（已取消关联）
- 因为协同报价单换绑后会从 status=1 变为 status=2，仅查 status=1 会漏掉已换绑的数据
- 已换绑判断：只要该报价单对应的 S 单**有一个**在当前合同上绑定，即认为已换绑

**封装方法**：
- `getBillCheckContext(contractCode)`：基于合同号获取需要校验换绑的单据信息，返回包含 boundSubOrderNos、billMap、validStandardBillCodes、validCooperBillCodes、validChangeOrderIds 的上下文对象
- `checkAndBuildResult(billCode, billTypeKey, expectedSubOrders, boundSubOrderNos)`：统一构建校验结果
- `isBillStatusValid(billStatus)`：判断报价单状态是否有效（非 IN_ADJUST、DELETED、CANCELED）

**返回格式**：
```json
{
  "C001": {
    "基础报价单校验": [
      {
        "基础报价单号": "B001",
        "应该换绑S单": ["S001", "S002", "S003"],
        "已换绑S单": ["S001", "S002"],
        "漏换绑S单": ["S003"],
        "是否正确": false
      }
    ],
    "变更单校验": [...],
    "协同报价单校验": [
      {
        "协同报价单号": "C001",
        "报价单状态": 1,
        "是否已换绑S单": false,
        "应该换绑S单": [],
        "已换绑S单": [],
        "漏换绑S单": [],
        "是否正确": true
      }
    ],
    "校验结果": "错误"
  }
}
```
