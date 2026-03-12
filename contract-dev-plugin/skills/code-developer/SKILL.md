---
description: 签约领域代码开发指南,包含领域特定的组件使用规范和开发工作流
---

# 签约系统代码开发指南

## 使用说明
在签约系统进行开发时,必须优先查阅本指南。

## 前置要求
- 开发前阅读 `../code-reader/references/base-domain-knowledge.md` 了解业务基础
- 遵循 TDD 开发规范: `../test-driven-development/SKILL.md`
- 代码审查标准: `../code-review/SKILL.md`

## 禁止耗时操作
- **严禁**在编写代码过程中进行耗时操作，包括但不限于：搜索本地 Maven 仓库（`~/.m2`）、下载依赖、反编译 JAR 包。
- 如需了解某个类或方法的签名，**只允许**在项目源码目录内搜索，或直接向用户提问，不得转而查找 Maven 缓存。

## 遇到不确定的情况立即提问
- 开发过程中遇到任何不清楚的地方（业务逻辑、字段含义、调用方式等），**必须立即询问用户**，严禁自行猜测或推断后直接编写代码。

---

## 基础组件使用规范

### 1. 文件上传 S3
**场景**: 需要将文件上传到 S3 存储服务
**规范文档**: [./references/file-upload-s3.md](./references/file-upload-s3.md)

### 2. 合同 PDF 变量传递
**场景**: 需要将业务数据传递到合同 PDF 生成服务
**规范文档**: [./references/contract-pdf-build-service.md](./references/contract-pdf-build-service.md)

### 3. RPC 调用规范
**场景**: 跨服务 RPC 调用(报价领域、主订单领域等)
**规范文档**: [./references/rpc-development.md](./references/rpc-development.md)

### 4. 定时任务开发规范
**场景**: 需要定期执行的后台任务(数据检查、状态同步、预警通知等)
**规范文档**: [./references/scheduled-task-development.md](./references/scheduled-task-development.md)

---

## 开发工作流

### 需求分析阶段
1. 理解业务背景和触发时机
2. 识别涉及的领域模型(报价单、合同等)
3. 查阅相关业务知识文档

### 设计阶段
1. 确定核心流程和关键步骤
2. 识别需要的服务和方法
3. 考虑异常场景和边界条件

### 开发阶段
1. **先写测试**(RED-GREEN-REFACTOR 循环)
2. 实现核心逻辑
3. 添加异常处理和日志
4. 代码审查(特别关注空指针安全)

### 测试阶段
1. 单元测试覆盖核心逻辑
2. 集成测试验证完整流程
3. 边界条件和异常场景测试

---

## 领域开发经验

### 报价单/变更单下单后绑定 S 单
**规范文档**: [./references/bill-to-suborder.md](./references/bill-to-suborder.md)

### 协同报价单撤回 - S 单撤回合同
**规范文档**: [./references/suborder-contract-revocation.md](./references/suborder-contract-revocation.md)

### 变更单取消时的合同处理
**规范文档**: [./references/change-order-cancel.md](./references/change-order-cancel.md)

### 获取主单号（projectOrderId）的正确方式

## 获取主单号的正确方式
### 业务背景
签约系统中存在两种获取 `projectOrderId` 的途径，但含义不同：
- `baseContractReq.getContractBaseInfo().getProjectOrderId()`：来自请求入参，是真正的**主单号**，用于调用主订单服务查询数据。
- `ContractContextHandler.getProjectInfo().getProjectOrderId()`：来自上下文，**可能不是主单号**（在某些场景下返回的是其他订单标识），直接用于主订单查询会导致报错。

### 触发时机
需要调用主订单服务（如查询 S 单、变更单等）时，需要传入 `projectOrderId` 参数的场景。

### 核心流程
**强制使用 `baseContractReq.getContractBaseInfo().getProjectOrderId()`** 获取主单号，禁止使用 `ContractContextHandler.getProjectInfo().getProjectOrderId()` 作为主订单查询的入参。

---

## 参考文档索引

### 业务知识
- 基础业务概念: `../code-reader/references/base-domain-knowledge.md`
- 销售合同流程: `../code-reader/references/personal-contract.md`

### 技术规范
- PDF 数据构造: `./references/contract-pdf-build-service.md`
- S3 文件上传: `./references/file-upload-s3.md`
- RPC 调用规范: `./references/rpc-development.md`
- 定时任务开发: `./references/scheduled-task-development.md`

### 质量保证
- TDD 规范: `../test-driven-development/SKILL.md`
- 代码审查标准: `../code-review/SKILL.md`
