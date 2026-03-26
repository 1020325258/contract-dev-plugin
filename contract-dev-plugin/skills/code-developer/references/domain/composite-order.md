# 组合单（CT单）与 S 单的关系

## 概述
组合单（CT单）是订单系统中的父单类型，一个组合单可以对应多个 S 单（子单）。在 BSU 拆单场景下，销售合同绑定关系需要从报价单调整为 S 单。

## 业务背景

### 术语澄清
- **组合单（CT单）**：对应 `OrderKindEnum.COMPOSIT_ORDER`，code=7
- **S 单**：子单，对应 `OrderKindEnum.SUB_ORDER`，code=2
- **compositeOrderNo**：组合单号，不是 S 单号

### 业务场景
BSU 拆单后：
1. 组合单下单 → 产生多个 S 单
2. 销售合同（PERSONAL 类型）从绑定报价单 → 绑定 S 单
3. 查询合同时需要通过组合单找到 S 单，再通过 S 单找到合同

## 核心流程

### 1. 查询组合单对应的 S 单

**RPC 接口**：`OrderQueryApi#queryRelatedOrderByOrderNo`

```java
// 入参
orderNo: 组合单号
orderKind: OrderKindEnum.COMPOSIT_ORDER.getCode() (7)

// 返回
CompositAndSubOrderDTO {
    String orderNo;                    // 组合单号
    List<SubOrderInfo> subOrderInfoList;  // S单列表
}

SubOrderInfo {
    String orderNo;                   // S单号
    Integer orderStatus;
}
```

### 2. S 单关联合同查询

**表**：`contract_quotation_relation`

**关键字段**：
- `bill_code`：绑定的单据编号（S 单号）
- `bind_type`：绑定类型
  - `1`（BILL_CODE）：报价单
  - `2`（CHANGE_ORDER）：变更单
  - `3`（SUB_ORDER）：S 单
- `status`：关联状态（1=已关联）
- `contract_code`：合同编号

### 3. 查询销售合同

**过滤条件**：
- `contract.type = 8`（`ContractTypeEnum.PERSONAL`）
- 签约人存在（`contract_user.is_sign = 1`）

## 方法示例

`CommonContractService#queryPersonalContractByCompositeOrderNos` 改造逻辑：

```
组合单号
  → RPC: queryRelatedOrderByCompositeOrderNo → S单列表
  → contract_quotation_relation(bind_type=3, status=1) → 合同编号
  → contract(type=8) + contract_user(is_sign=1)
  → PersonalContractDTO
```

## 注意事项

1. **一个组合单对应多个 S 单**：查询结果取第一个有关联合同的 S 单即可
2. **bind_type=3 表示 S 单关联**：查询合同关联时需指定 `bindType=BindTypeEnum.SUB_ORDER`
3. **术语准确性**：compositeOrderNo 是组合单号，不是 S 单号

## 相关链接
- [RPC 调用规范](../technical/rpc-development.md)
- [ContractQuotationRelation 表结构](../infrastructure/contract-database-tables.md)
