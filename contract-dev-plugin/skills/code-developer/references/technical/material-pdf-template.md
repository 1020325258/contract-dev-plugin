---
name: material-pdf-template
description: 辅材清单 PDF 模板文件的位置、Thymeleaf 变量结构及说明文案
---

# 辅材清单 PDF 模板

## 概述

辅材清单以 Thymeleaf HTML 模板渲染为 PDF，修改展示样式或文案时需找到该模板文件。

## 模板位置

```
utopia-nrs-sales-project-start/src/main/resources/templates/pdftemplate/material.html
```

## 模板变量结构

模板接收变量 `materialItems`，为列表，每项包含以下字段：

| 字段 | 说明 |
|------|------|
| `item.sequenceNumber` | 序号 |
| `item.categoryLevel3Name` | 类别（三级品类名称） |
| `item.brandNames` | 品牌名称（多个品牌拼接的字符串） |

### 品牌单元格渲染示例

```html
<td>
    <span th:text="${item.brandNames}"></span>
</td>
```

> 注意：品牌列只渲染 `brandNames` 字段内容，无需在模板中追加"等其他同档次品牌"等固定文案（该文案已于 2026-03-26 移除）。

## 说明文案（当前版本）

```
说明：乙方会根据产品质量等因素对供应商进行不定期考核筛查，力求为客户提供更优质的产品和服务。
若因供应商合作调整、产能调整、物流配送波动等客观因素导致上述辅料品牌发生更迭，乙方将提供现期所合作的其他同档次品牌。
```

## 相关链接

- [PDF 数据构造](./contract-pdf-build-service.md) - Java 服务端如何向 PDF 模板传递数据
