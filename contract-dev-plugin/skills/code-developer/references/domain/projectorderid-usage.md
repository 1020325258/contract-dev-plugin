# 获取主单号的正确方式

## 概述
签约系统中存在两种获取 `projectOrderId` 的途径，但含义不同，误用会导致主订单查询报错。

## 业务背景
- `baseContractReq.getContractBaseInfo().getProjectOrderId()`：来自请求入参，是真正的**主单号**，用于调用主订单服务查询数据。
- `ContractContextHandler.getProjectInfo().getProjectOrderId()`：来自上下文，**可能不是主单号**（在某些场景下返回的是其他订单标识），直接用于主订单查询会导致报错。

## 使用规范
**强制使用** `baseContractReq.getContractBaseInfo().getProjectOrderId()` 获取主单号。

**禁止使用** `ContractContextHandler.getProjectInfo().getProjectOrderId()` 作为主订单查询的入参。

## 触发场景
需要调用主订单服务（如查询 S 单、变更单等）时，需要传入 `projectOrderId` 参数的场景。
