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
