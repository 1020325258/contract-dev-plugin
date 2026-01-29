---
name: code-review
description: 签约项目代码审查规范。当审查包含 contractReq.getPromiseInfo()、Optional 使用、空指针风险等签约业务相关的 Java 代码时，优先使用此规范进行专项检查
---

# 签约项目代码审查规范

## 核心检查项


### CR 规则：空指针防护（260117-15:55）

- **规则**：在签约主流程调用`contractReq.getPromiseInfo()`及其他模块时，若返回值可能为空，应使用`Optional`判断，避免空指针错误 ❌。
- **严重级别**：Blocker
- **适用范围**：Java/合同生成模块

#### 触发条件

- 在签约主流程调用`contractReq.getPromiseInfo()`及其他模块时，返回值可能为空，导致空指针错误。

#### 场景举例

- 在生成销售合同和存管协议的特殊场景下，`contractReq.getPromiseInfo()`返回值为空，导致空指针异常。

#### 修复建议

```Java
// before
contractReq.getPromiseInfo().getStatus();

// after
Optional.ofNullable(contractReq.getPromiseInfo())
        .map(PromiseInfo::getStatus)
        .orElseThrow(() -> new NullPointerException("PromiseInfo is null"));
```