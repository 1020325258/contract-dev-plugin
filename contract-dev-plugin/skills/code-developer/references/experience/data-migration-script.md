# 刷数脚本开发规范

## 概述
数据刷数脚本的开发规范，包括小范围验证机制、类型过滤优化等最佳实践。

## 背景
刷数脚本通常涉及大量数据更新，一旦逻辑错误可能导致严重后果。因此需要设计小范围验证机制，确保逻辑正确后再全量执行。

## 核心规范

### 1. 必须支持 startId/endId 参数

**目的**：支持小范围验证，避免全量刷数导致不可逆后果。

**参考模式**（来自 `ConfigSyncSchedule#completedConfigSyncOfContractAndPay`）：

```java
public void repairAll(Long startId, Long endId) {
    LOGGER.info("[刷数]开始刷数，startId={}, endId={}", startId, endId);
    while (true) {
        Example example = new Example(ContractQuotationRelation.class);
        Example.Criteria criteria = example.createCriteria()
            .andEqualTo("status", RelationStatusEnum.RELATED.getCode())
            .andEqualTo("delStatus", 0);
        // 支持按 ID 范围过滤
        if (startId != null) {
            criteria.andGreaterThanOrEqualTo("id", startId);
        }
        if (endId != null) {
            criteria.andLessThanOrEqualTo("id", endId);
        }
        example.orderBy("id").asc();
        // ... 分页处理
    }
}
```

**验证流程**：
1. 先用 `startId=1&endId=10` 验证前 10 条
2. 检查日志确认逻辑正确
3. 确认无误后再全量刷数

### 2. 类型过滤前置

**问题**：如果循环内对每条数据都做类型判断，会导致大量重复查询。

**优化方案**：在进入循环之前，先批量过滤掉不符合条件的数据。

**错误示例**：
```java
// processRelationsBatch 内部再过滤
private long processRelationsBatch(List<ContractQuotationRelation> relations) {
    Map<String, Contract> contractMap = contracts.stream()
        .filter(c -> ContractTypeEnum.PERSONAL.getCode().equals(c.getType())) // 循环内过滤
        .collect(Collectors.toMap(...));
    // ...
}
```

**正确示例**：
```java
// 在调用 processRelationsBatch 之前先过滤
private void repairAll(Long startId, Long endId) {
    // ...
    // 过滤非销售合同的关联关系
    List<ContractQuotationRelation> personalRelations = filterPersonalContractRelations(relations);
    if (CollectionUtils.isEmpty(personalRelations)) {
        LOGGER.info("[刷数]当前批次无目标数据，跳过，pageNum={}", pageNum);
        continue;
    }
    long processed = processRelationsBatch(personalRelations);
    // ...
}

// 提取公共过滤方法
private List<ContractQuotationRelation> filterPersonalContractRelations(List<ContractQuotationRelation> relations) {
    List<String> contractCodes = relations.stream()
        .map(ContractQuotationRelation::getContractCode)
        .distinct()
        .collect(Collectors.toList());
    List<Contract> contracts = contractService.getListByContractCodes(contractCodes, true);

    Set<String> personalContractCodes = contracts.stream()
        .filter(c -> ContractTypeEnum.PERSONAL.getCode().equals(c.getType()))
        .map(Contract::getContractCode)
        .collect(Collectors.toSet());

    return relations.stream()
        .filter(r -> personalContractCodes.contains(r.getContractCode()))
        .collect(Collectors.toList());
}
```

### 3. 方法职责清晰

**原则**：
- 过滤方法只负责过滤
- 处理方法假设数据已过滤，不再重复判断

**好处**：
- 避免重复逻辑
- 方法职责单一，易于测试

### 4. 防误调用机制

**Controller 层必须加时间校验**：

```java
@PostMapping("/api/contract/tool/repairContractQuotationRelation")
public ResultDTO<String> repairContractQuotationRelation(
        @RequestParam("time") @DateTimeFormat(pattern = "yyyy-MM-dd HH:mm:ss") Date clientTime,
        @RequestParam(value = "startId", required = false) Long startId,
        @RequestParam(value = "endId", required = false) Long endId) {
    // 校验传入时间，防止误调用
    long now = System.currentTimeMillis();
    long diff = Math.abs(now - clientTime.getTime());
    if (diff > 5 * 60 * 1000) {
        return new ResultDTO<String>().fail("时间校验失败，请确认请求时间与服务器时间相差不超过5分钟");
    }
    // ...
}
```

## 相关文档
- [测试开发规范](../workflow/testing.md) - 刷数脚本必须编写单元测试
