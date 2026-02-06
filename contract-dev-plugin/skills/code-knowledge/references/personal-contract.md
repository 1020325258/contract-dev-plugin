---
name: personal-contract
description: 记录签约领域内部涉及的销售合同、报价单、报价领域交互逻辑。
---

# 个性化合同业务逻辑

## 报价单撤回监听器 (CancelPersonalContractListener)

### 职责描述

监听 Kafka 消息，当个性化报价单从正式版状态回退到调整中/已提交状态时，自动处理关联合同。

### 触发条件

```java
// 监听事件类型
@EventType(bizType = "utopia-athena-domain-entity-bizType", serverName = "utopia-athena")

// 处理报价单类型
- AthenaDomainEntityTypeEnum.SIGN_COOPER_BUDGET_BILL (协同报价单)
- AthenaDomainEntityTypeEnum.GROUP_BUDGET_BILL (团签报价单)

// 撤回状态判定
Map<sourceStatus, List<targetStatus>>:
  3 → [1, 2]  // 正式版 → 调整中/已提交
  2 → [1]     // 已提交 → 调整中
```

### 核心处理流程

#### 1. 前置操作
```java
// CancelPersonalContractListener.java:111
homeOrderOperationService.revokeQuote(billCode, orderKind, projectOrderId);
```

#### 2. 已绑定报价单的合同处理

**查询路径：**
```java
// CancelPersonalContractListener.java:115
quotationRelationCommonService.getContractByBillCode(billCode)
  → 返回关联该报价单的合同列表
```

**跳过条件 (不处理的合同)：**
```java
// CancelPersonalContractListener.java:120
- contract == null
- status = CANCEL (已取消)
- status IN SIGNED_STATUS_LIST (已签约)
- status = PENDING_USER_SIGN && userConfirmStatus = YES (用户已确认待签约)
- contractQuotationRelationList.isEmpty() (无有效绑定关系)
```

**场景分支：**

| 条件 | 操作 | 代码位置 |
|-----|------|---------|
| 仅绑定该报价单 | 取消绑定关系 + 取消合同 | :124-126 |
| 绑定多个报价单 | 解除单个绑定 + 回退合同到草稿 | :127-135 |

**关键方法调用：**
```java
// 场景1：仅绑定该报价单
quotationRelationCommonService.cancelRelationByBillCode(contractCode);
commonContractService.cancelCurrentContract(contract, operatorUcid, true);

// 场景2：绑定多个报价单
quotationRelationCommonService.cancelRelationByBillCodeAndContractCode(contractCode, billCode);
homeAndPcCommonService.undoContract(contract, operatorUcid);
```

#### 3. 正签合同字段同步

```java
// CancelPersonalContractListener.java:138-162

// 查询关联的正签合同
ContractRelation contractRelation = contractRelationService.getByRelateContractCode(contractCode);

// 更新正签合同字段：移除撤回的报价单
字段1: billCodeInfoList (List<BillCodeInfo>)
字段2: billCodeList (List<String>)

// 操作
contractFieldService.updateContractField(contractCode, fieldKey, fieldValue);
```

#### 4. 历史未绑定报价单的合同处理

**查询路径：**
```java
// CancelPersonalContractListener.java:167
contractService.getLatestContractByStatus(
  projectOrderId,
  ContractTypeEnum.PERSONAL.getCode(),
  [DRAFT, PENDING_USER_CONFIRM, PENDING_USER_SIGN, PENDING_SUBMIT_AUDIT, AUDITING, PENDING_COMPANY_SIGN]
)
```

**判定逻辑：**
```java
// CancelPersonalContractListener.java:174-184
ContractField contractField = contractFieldService.getByContractCodeAndKey(contractCode, "billCodeList");
List<String> billCodeList = JSON.parseArray(fieldValue, String.class);

if (billCodeList.contains(billCode)) {
    commonContractService.cancelCurrentContract(contract, operatorUcid, true);
}
```

### 数据结构

#### KafkaMessageAthenaDomainEntityEventDTO
```
projectOrderId   项目订单ID
entityType       实体类型 (协同报价单/团签报价单)
billCode         报价单编号
sourceStatus     原状态 (3=正式版, 2=已提交)
entityStatus     目标状态 (1=调整中, 2=已提交)
operatorUcid     操作人ID
```

#### 合同字段 (ContractField)
```
billCodeList       报价单编号列表 (List<String>)
billCodeInfoList   报价单详情列表 (List<BillCodeInfo>)
```

### 幂等性保护

通过状态判断避免重复处理：
- 已取消合同：跳过
- 已签约合同：跳过
- 用户已确认待签约：跳过

### 级联影响

```
个性化合同撤回
  ├─ 解除绑定关系 (ContractQuotationRelation)
  ├─ 更新合同状态 (Contract)
  └─ 同步正签合同字段 (ContractField)
      ├─ billCodeList
      └─ billCodeInfoList
```

