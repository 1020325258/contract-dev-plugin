---
name: layering-design
description: Service 与 Repository 的职责边界，避免业务逻辑下沉到 DB 层
---

# 分层设计原则：Service vs Repository 职责边界

## 概述

业务判断逻辑必须放在 Service 层，Repository 层只做纯 DB 操作。

## 规则

**Service 层负责**：
- 根据入参决定调用哪个 Repository 方法（业务分支）
- 例：`comboCodes` 为空 → 调 `deleteAll()`；否则 → 调 `deleteByComboCodes(comboCodes)`

**Repository 层负责**：
- 执行具体的 SQL 操作，不含业务判断
- 例：`deleteByComboCodes` 只做 `WHERE combo_code IN (...)` 的软删除

## 反模式（❌ 不要这样写）

```java
// ❌ 错误：Repository 层混入业务逻辑
public void deleteByComboCodes(List<String> comboCodes) {
    if (CollectionUtils.isEmpty(comboCodes)) {
        deleteAll();  // 业务判断不属于这里
        return;
    }
    // ...
}
```

## 正确写法

```java
// ✅ 正确：业务判断在 Service 层
public void clearComboMaterialCache(List<String> comboCodes) {
    if (CollectionUtils.isEmpty(comboCodes)) {
        contractMaterialPdfDataRepository.deleteAll();
    } else {
        contractMaterialPdfDataRepository.deleteByComboCodes(comboCodes);
    }
}

// ✅ 正确：Repository 只做 DB 操作
public void deleteByComboCodes(List<String> comboCodes) {
    Example example = new Example(ContractMaterialPdfData.class);
    example.createCriteria().andIn(ContractMaterialPdfData.Fields.comboCode, comboCodes);
    contractMaterialPdfDataMapper.deleteSoftByExample(example);
}
```
