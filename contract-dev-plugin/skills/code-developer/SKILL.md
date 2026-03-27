---
description: 签约领域代码开发指南。当用户询问签约业务开发、修改签约代码、阅读签约领域代码，或当前工作目录为 nrs-sales-project 时自动触发。包含领域特定的组件使用规范和开发工作流。
---

# 签约系统代码开发指南

## 前置要求
- 开发前阅读 `./references/domain/base-domain-knowledge.md` 了解业务基础
- 遵循测试开发规范: `./references/workflow/testing.md`
- 代码审查标准: `../reviewer/SKILL.md`

## 代码阅读规范
- 涉及枚举类时**必须**到枚举类定义中查看确切含义，不能仅凭枚举常量名称推测业务含义。
- 确保所有描述准确，特别是业务术语，务必基于领域知识文档中的概念。

---

## 禁止事项

### ⚠️ 插件文件修改必须写入源码目录
| 路径 | 说明 |
|---|---|
| ✅ `/Users/zqy/work/AI-Project/claude-code-plugins/sales-project-plugins/contract-dev-plugin/` | **源码目录**，所有修改必须写这里 |
| ❌ `~/.claude/plugins/marketplaces/contract-marketplace/contract-dev-plugin/` | 缓存目录，**禁止直接修改** |

### 禁止耗时操作
- **严禁**搜索本地 Maven 仓库（`~/.m2`）、下载依赖、反编译 JAR 包
- 如需了解类/方法签名，**只允许**在项目源码目录内搜索，或直接向用户提问

### 遇到不确定立即提问
- 业务逻辑、字段含义、调用方式等不清楚时，**必须立即询问用户**

---

## 知识索引

### 业务领域 (domain)
- [基础业务概念](./references/domain/base-domain-knowledge.md) - 报价单、合同核心模型、领域术语
- [销售合同流程](./references/domain/personal-contract.md) - 个性化报价单撤回、基础报价单拆分换绑
- [报价单绑定 S 单](./references/domain/bill-to-suborder.md) - 报价单/变更单下单后与 S 单的绑定
- [组合单与 S 单](./references/domain/composite-order.md) - 组合单(CT单)与S单的关系、销售合同绑定S单逻辑
- [S 单撤回合同](./references/domain/suborder-contract-revocation.md) - 协同报价单/变更单撤回时的合同处理
- [变更单取消处理](./references/domain/change-order-cancel.md) - 变更单取消时的合同状态处理
- [获取主单号正确方式](./references/domain/projectorderid-usage.md) - projectOrderId 的正确获取途径

### 技术规范 (technical)
- [RPC 调用规范](./references/technical/rpc-development.md) - 跨服务 RPC 调用规范
- [分布式锁规范](./references/technical/distributed-lock.md) - LockService 超时行为、锁 key 常量、死锁分析
- [S3 文件上传](./references/technical/file-upload-s3.md) - 文件上传到 S3 存储服务
- [PDF 数据构造](./references/technical/contract-pdf-build-service.md) - 合同 PDF 变量传递
- [辅材清单 PDF 模板](./references/technical/material-pdf-template.md) - 模板位置、Thymeleaf 变量结构、说明文案
- [定时任务开发](./references/technical/scheduled-task-development.md) - 后台定时任务开发规范

### 开发工作流 (workflow)
- [测试开发规范](./references/workflow/testing.md) - TDD 原则、测试覆盖矩阵、纯 Mock 测试、集成测试继承 BaseTest、代码修改同步调用方
- [Maven 测试问题排查](./references/workflow/maven-test-troubleshooting.md) - 测试执行常见问题
- [SREmate 测试运行规范](./references/workflow/sremate-testing.md) - 按变更范围精确选择测试，节省 token
- [分层设计原则](./references/workflow/layering-design.md) - Service 做业务判断，Repository 只做纯 DB 操作
- Ralph Loop: 见 `../ralph-wiggum/SKILL.md`

### 实践经验 (experience)
- [Lombok @Slf4j 规范](./references/experience/lombok-sl4fj-usage.md) - 日志必须使用 @Slf4j + LOGGER，禁止使用 log 或自行创建 Logger

### 基础设施 (infrastructure)
- [数据库表结构](./references/infrastructure/contract-database-tables.md) - 合同领域表结构、字段含义

### 关联规范
- 代码审查: `../reviewer/SKILL.md`
