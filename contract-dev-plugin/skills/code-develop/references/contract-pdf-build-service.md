---
name: contract-pdf-build-service
description: ContractPdfBuildService 类的知识库，用于理解合同 PDF 生成时的数据计算逻辑。当需要了解合同 PDF 字段来源时，应优先参考此文档。
---

# ContractPdfBuildService 类知识库

## 职责描述

`ContractPdfBuildService` 是合同 PDF 生成的核心数据构建服务，负责为合同模板提供所有需要填充的业务数据。该类通过反射调用方法，将各种业务数据封装为 `Map<String, Object>` 格式，供 PDF 模板渲染使用。

## 如何查看合同 PDF 字段的数据来源？
1. 当用户询问某个变量的来源：
在 `ContractPdfBuildService` 服务中，所有传递给合同 PDF 的变量都会放入到 `Map<String, Object> result = new HashMap<>();` 内部。
当用户询问某个变量来源，直接查询 `result.put(key, value);` 中 value 的来源。



2. 当用户询问某个方法传递的数据：
在 `ContractPdfBuildService` 服务中，找到通过 `result.put(key, value)` 放入的值，找到 value 的来源。


### 示例
在 `ContractPdfBuildService#getStructureInfo()` 方法中，通过 `result.put()` 向合同 PDF 传递了 6 个变量值，key 分别为 `structure、roomCnt、parlorCnt、cookroomCnt、toiletCnt、balconyCnt`，对应的变量值来源于 `ContractContextHandler.getContractReq().getProjectInfo()` 内部的属性。
```java
public Map<String, Object> getStructureInfo() {
    HashMap<String, Object> result = new HashMap<>();
    ContractProjectInfoReq projectInfo = ContractContextHandler.getContractReq().getProjectInfo();
    //住宅结构
    result.put("structure", Optional.ofNullable(StructureEnum.getNameByCode(projectInfo.getStructure())).orElse(""));
    //室数
    result.put("roomCnt", String.valueOf(projectInfo.getRoomCnt()));
    //厅数
    result.put("parlorCnt", String.valueOf(projectInfo.getParlorCnt()));
    //厨房数
    result.put("cookroomCnt", String.valueOf(projectInfo.getCookroomCnt()));
    //卫生间数
    result.put("toiletCnt", String.valueOf(projectInfo.getToiletCnt()));
    //阳台数
    result.put("balconyCnt", String.valueOf(projectInfo.getBalconyCnt()));
    return result;
}
```
