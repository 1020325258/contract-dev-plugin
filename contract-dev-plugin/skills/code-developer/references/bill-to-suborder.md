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
- 正签基础报价单：仅绑定 S 单，保留基础报价单关联（`convertBasicBillToSubOrder`）
- 变更单：仅绑定 S 单，保留变更单关联（`convertChangeToSubOrder`）
