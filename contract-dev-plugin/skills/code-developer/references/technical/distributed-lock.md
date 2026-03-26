# 分布式锁使用规范（LockService）

## 概述
`LockService` 封装了 Redisson 分布式锁，理解其超时行为和锁 key 设计可避免逻辑缺失或死锁分析误判。

## 核心行为：超时后操作不会执行

```java
lockService.lockElseThrow(lockKey, () -> {
    // 若 maxWaitMillis 内未抢到锁，这里不会执行
    doSomething();
    return null;
});
```

**调用链**：
1. `lockElseThrow(key, Supplier)` → 调用 `lockElseThrow(key)`
2. 执行 `lock.tryLock(maxWaitMillis, LOCK_SECONDS, TimeUnit.MILLISECONDS)`
3. 若 `success = false`，**直接抛出 `NrsBusinessException(LOCK_LIMIT)`**，Supplier 不会执行

**默认等待时间**：`DEFAULT_MAX_WAIT_MILLIS = 1000ms`（可通过重载方法传入自定义值，如 10000ms）

**锁持有时间**：`LOCK_SECONDS = 60000ms`，Redisson watchdog 机制会在业务执行期间自动续期

## 常用重载形式

| 方法签名 | 等待时间 | 适用场景 |
|---------|---------|---------|
| `lockElseThrow(key, Supplier)` | 1000ms（默认） | 并发冲突少、快速失败场景 |
| `lockElseThrow(key, Supplier, 10000)` | 10000ms | 业务竞争明显、等待代价低 |
| `lockElseThrow(key)` 返回 RLock | 1000ms | 需要手动释放锁的场景 |

## 锁 Key 常量（LockService 中定义）

| 常量 | 用途 |
|-----|-----|
| `CONTRACT_RELATION_BILL_CODE` | 报价单换绑 S 单 / 协同报价单撤回互斥 |
| `CONTRACT_CODE` | 合同级别操作互斥 |
| `PROJECT_ORDER_ID` | 项目订单级别操作互斥 |

## 死锁风险分析

**不会死锁的典型场景**：

`revokeCooperQuotation`（撤回）和 `convertCooperBillToSubOrderByContract`（换绑）对同一 `cooperBillCode` 加锁：
- 两个方法使用**同一个 key**，是互斥竞争关系，不是循环等待
- 死锁要求：线程 A 持有锁1等待锁2，线程 B 持有锁2等待锁1
- 这里每个方法只持有一把锁，不满足死锁条件
- `tryLock` 有超时，即使极端情况下也会退出，不会无限等待

**需要注意的场景**：for 循环中串行加锁（如遍历多个 cooperBillCode），每次只持有一把锁，循环体内不嵌套加其他锁 → 安全。

## 调用方异常处理差异

同一个 `convertCooperBillToSubOrderByContract` 被不同调用方以不同方式调用：

| 调用方 | 调用方式 | 超时后效果 |
|-------|---------|-----------|
| `ContractSubmitListener` | `CompletableFuture.runAsync` + `exceptionally` | 异常被吞，操作静默丢失 |
| `BillToSubOrderListener` | 同步调用 | 异常上抛，Kafka 消息重试 |
| `BudgetBillSplitHandlerV2` | 同步调用（forEach 内） | 异常上抛，forEach 中断 |
