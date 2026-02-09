---
description: 签约领域知识文档，阅读或者开发代码之前优先阅读当前文档。
---

## 职责
整理了签约系统内部的代码与业务信息之间的关联关系，在阅读和开发代码之前，先阅读当前文档，以提高准确性。

### 相关文档
- 签约领域基础知识(**在阅读或开发代码之前，必须阅读该文档**)：`./references/base-domain-knowledge.md`
- 销售合同/报价相关规则：`./references/personal-contract.md`
- 合同 PDF 数据构造规则：`./references/contract-pdf-build-service.md`
- 通用文档：
    - mvm test 无法正确执行解决文档：`./references/maven-test-troubleshooting.md`
详细内容：描述数据是如何通过前端页面传递至后端服务，在后端服务内部计算之后，传输至合同 PDF；ContractPdfBuildService 内部的各个方法通过反射调用，方法的返回值会作为合同 PDF 的变量生成最终合同。



