---
name: code-knowledge
description: 签约项目业务信息文档，阅读或者开发代码之前优先阅读当前文档。
---

## 职责
整理了签约系统内部的代码与业务信息之间的关联关系，在阅读和开发代码之前，先阅读当前文档，以提高准确性。

### 相关文档
- 业务术语词汇表：./references/
- 合同 PDF 数据构造规则：./references/contract-pdf-build-service.md
详细内容：描述数据是如何通过前端页面传递至后端服务，在后端服务内部计算之后，传输至合同 PDF；ContractPdfBuildService 内部的各个方法通过反射调用，方法的返回值会作为合同 PDF 的变量生成最终合同。



