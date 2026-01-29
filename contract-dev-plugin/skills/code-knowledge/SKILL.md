---
name: code-knowledge
description: 签约项目知识信息，描述了代码内部的数据来源和流转规则。
---

## 职责
描述数据是如何通过前端页面传递至后端服务，在后端服务内部计算之后，传输至合同 PDF。

- 数据传递至合同 PDF：ContractPdfBuildService 内部的各个方法通过反射调用，方法的返回值会作为合同 PDF 的变量生成最终合同。文档：./references/contract-pdf-build-service.md