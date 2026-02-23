---
name: contract-pdf-build-service
description: ContractPdfBuildService 开发规范,用于理解合同 PDF 生成时的数据计算逻辑和反射调用机制
---

# ContractPdfBuildService 开发规范

## 职责描述

`ContractPdfBuildService` 是合同 PDF 生成的核心数据构建服务,负责为合同模板提供所有需要填充的业务数据。

**位置**: `com.ke.utopia.nrs.salesproject.service.contract.v2.ContractPdfBuildService`

**核心特点**:
- 类内所有方法均通过**反射调用**,方法名配置在数据库表 `contract_protocol_config` 中
- 每个方法返回 `Map<String, Object>`,key 为 PDF 字段名,value 为字段值
- 方法通过 `formId` (合同模板ID) 关联配置

---

## 反射调用机制

### 核心流程

```
合同生成PDF
    ↓
根据 formId 查询数据库配置
    ↓
获取 dealFunction 方法列表
    ↓
反射调用 ContractPdfBuildService 的方法
    ↓
合并所有方法返回的 Map
    ↓
传输给协议平台生成 PDF
```

### 数据库配置表: contract_protocol_config

| 字段 | 说明 | 示例 |
|-----|------|------|
| `form_id` | 合同模板 ID | 12345 |
| `form_key` | 合同模板 key | "personal_contract" |
| `form_field_key` | PDF 字段 key | "contractNo" |
| `form_field_name` | PDF 字段名称 | "合同编号" |
| `deal_function` | **处理方法名** | "getContractNo" |
| `allow_blank` | 是否允许为空 | 0/1 |

**关键点**:
- `deal_function` 字段存储方法名,如 `"getContractNo"`
- 多个字段可以配置相同的 `deal_function`,方法返回的 Map 包含多个字段

### 反射调用代码

**位置**: `ContractPdfCreateService#buildFormData`

```java
public Map<String, Object> buildFormData(Set<String> dealFunctions){
    /**
     * 数据库 dealFunction 配置了每个字段的获取方法名
     * contractPdfBuildService 封装了所有方法的实现
     * 通过反射，获取请求协议平台的每个字段的值
     */
    Map<String, Object> formData = new HashMap<>();

    for (String dealFunction : dealFunctions) {
        try {
            // 1. 通过反射获取方法
            Method method = contractPdfBuildService.getClass()
                .getMethod(dealFunction, null);

            // 2. 调用方法获取返回值
            Map invokeResult = (Map) method.invoke(contractPdfBuildService, null);

            // 3. 合并到 formData
            formData.putAll(invokeResult);

            LOGGER.info("pdf生成时，调用方法{}返回结果为：{}",
                dealFunction, invokeResult);

        } catch (NoSuchMethodException e) {
            LOGGER.error("pdf生成时，调用方法不存在,方法名：{}", dealFunction, e);
            throw new NrsBusinessException(ResultCodeEnum.ERROR_BUSINESS.getCode(),
                e.getMessage());
        }
    }
    return formData;
}
```

---

## 开发规范

### 1. 方法命名规范

**重要提示**: 类注释已明确说明
```java
/**
 * 合同生成pdf构建服务
 * 方法均未反射调用，方法勿删，勿改名!!!
 * 方法均未反射调用，方法勿删，勿改名!!!
 * 方法均未反射调用，方法勿删，勿改名!!!
 */
```

**规范**:
- ✅ 方法名必须与数据库 `deal_function` 字段配置一致
- ✅ 使用驼峰命名: `getContractNo`、`getStructureInfo`
- ✅ 以 `get` 开头,清晰表达获取的数据类型
- ❌ 禁止修改方法名,会导致反射调用失败
- ❌ 禁止删除方法,即使看起来没有直接调用

### 2. 方法签名规范

```java
// ✅ 正确: 无参数,返回 Map<String, Object>
public Map<String, Object> getContractNo() {
    HashMap<String, Object> result = new HashMap<>();
    // ...
    return result;
}

// ❌ 错误: 不要添加参数
public Map<String, Object> getContractNo(String param) {
    // 反射调用会失败
}

// ❌ 错误: 返回类型必须是 Map
public String getContractNo() {
    // 反射调用会类型转换失败
}
```

**要求**:
- 方法必须是 `public`
- 无参数 (反射调用时传 `null`)
- 返回类型: `Map<String, Object>`

### 3. Map 数据构建规范

```java
public Map<String, Object> getStructureInfo() {
    HashMap<String, Object> result = new HashMap<>();

    // 1. 获取上下文数据
    ContractProjectInfoReq projectInfo =
        ContractContextHandler.getContractReq().getProjectInfo();

    // 2. 构建 Map,key 为 PDF 字段名
    result.put("structure",
        Optional.ofNullable(StructureEnum.getNameByCode(projectInfo.getStructure()))
            .orElse(""));
    result.put("roomCnt", String.valueOf(projectInfo.getRoomCnt()));
    result.put("parlorCnt", String.valueOf(projectInfo.getParlorCnt()));
    result.put("cookroomCnt", String.valueOf(projectInfo.getCookroomCnt()));
    result.put("toiletCnt", String.valueOf(projectInfo.getToiletCnt()));
    result.put("balconyCnt", String.valueOf(projectInfo.getBalconyCnt()));

    return result;
}
```

**关键点**:
- Map 的 key 必须与协议平台配置的字段名一致
- 使用 `Optional` 处理可能为 null 的数据
- 数值类型转换为 String
- 枚举值转换为中文描述

### 4. 数据来源规范

数据主要来自 `ContractContextHandler`:

```java
// 获取合同请求上下文
ContractReq contractReq = ContractContextHandler.getContractReq();

// 常用数据来源
contractReq.getContract();        // 合同基础信息
contractReq.getProjectInfo();     // 项目信息
contractReq.getCustomerInfo();    // 客户信息
contractReq.getPromiseInfo();     // 承诺信息 (可能为 null)
contractReq.getCompanyInfo();     // 公司信息
```

**空指针安全**:
```java
// ✅ 正确: 使用 Optional 处理可能为 null 的数据
Optional.ofNullable(contractReq.getPromiseInfo())
    .map(PromiseInfo::getStatus)
    .orElse("");

// ❌ 错误: 直接调用可能为 null 的对象
contractReq.getPromiseInfo().getStatus();  // 可能 NPE
```

### 5. 异常处理规范

```java
public Map<String, Object> getContractNo() {
    HashMap<String, Object> result = new HashMap<>();

    try {
        ContractReq contractReq = ContractContextHandler.getContractReq();
        Contract contract = contractReq.getContract();

        // 业务逻辑...
        result.put("contractNo", contract.getContractNo());

    } catch (Exception e) {
        // 记录日志并抛出业务异常
        LOGGER.error("获取合同编号失败", e);
        throw new NrsBusinessException("获取合同编号失败: " + e.getMessage());
    }

    return result;
}
```

**要求**:
- 捕获异常并记录日志
- 抛出 `NrsBusinessException`,提供清晰的错误信息
- 不要吞掉异常,会导致 PDF 生成缺失字段

---

## 完整示例

### 示例 1: 简单字段获取

```java
/**
 * 获取合同编号
 * 对应 PDF 字段: contractNo
 */
public Map<String, Object> getContractNo() {
    HashMap<String, Object> result = new HashMap<>();

    ContractReq contractReq = ContractContextHandler.getContractReq();
    Contract contract = contractReq.getContract();

    result.put("contractNo", contract.getContractNo());

    return result;
}
```

### 示例 2: 多个字段构建

```java
/**
 * 获取房屋结构信息
 * 对应 PDF 字段: structure, roomCnt, parlorCnt, cookroomCnt, toiletCnt, balconyCnt
 */
public Map<String, Object> getStructureInfo() {
    HashMap<String, Object> result = new HashMap<>();

    ContractProjectInfoReq projectInfo =
        ContractContextHandler.getContractReq().getProjectInfo();

    // 住宅结构 - 枚举转中文
    result.put("structure",
        Optional.ofNullable(StructureEnum.getNameByCode(projectInfo.getStructure()))
            .orElse(""));

    // 数值转字符串
    result.put("roomCnt", String.valueOf(projectInfo.getRoomCnt()));
    result.put("parlorCnt", String.valueOf(projectInfo.getParlorCnt()));
    result.put("cookroomCnt", String.valueOf(projectInfo.getCookroomCnt()));
    result.put("toiletCnt", String.valueOf(projectInfo.getToiletCnt()));
    result.put("balconyCnt", String.valueOf(projectInfo.getBalconyCnt()));

    return result;
}
```

### 示例 3: 处理可能为 null 的数据

```java
/**
 * 获取承诺信息
 * 对应 PDF 字段: promiseStatus
 * 注意: promiseInfo 可能为 null
 */
public Map<String, Object> getPromiseInfo() {
    HashMap<String, Object> result = new HashMap<>();

    ContractReq contractReq = ContractContextHandler.getContractReq();

    // 使用 Optional 处理可能为 null 的数据
    String promiseStatus = Optional.ofNullable(contractReq.getPromiseInfo())
        .map(PromiseInfo::getStatus)
        .map(PromiseStatusEnum::getNameByCode)
        .orElse("");

    result.put("promiseStatus", promiseStatus);

    return result;
}
```

### 示例 4: 复杂数据处理

```java
/**
 * 获取付款计划信息
 * 对应 PDF 字段: payPlanInfo (格式化后的付款计划文本)
 */
public Map<String, Object> getPayPlanInfo() {
    HashMap<String, Object> result = new HashMap<>();

    ContractReq contractReq = ContractContextHandler.getContractReq();
    List<PayPlan> payPlans = contractReq.getPayPlans();

    if (CollectionUtils.isEmpty(payPlans)) {
        result.put("payPlanInfo", "");
        return result;
    }

    // 格式化付款计划
    StringBuilder payPlanInfo = new StringBuilder();
    for (int i = 0; i < payPlans.size(); i++) {
        PayPlan plan = payPlans.get(i);

        String formatted = String.format(
            "【%s】，甲方支付工程款的【%s】%%，即%s；",
            plan.getStageName(),
            plan.getPaymentRatio(),
            MoneyConvertUtil.convertToChineseMoney(plan.getAmount())
        );

        payPlanInfo.append(formatted);
        if (i < payPlans.size() - 1) {
            payPlanInfo.append("\n");
        }
    }

    result.put("payPlanInfo", payPlanInfo.toString());

    return result;
}
```

---

## 新增方法流程

### 1. 在 ContractPdfBuildService 中添加方法

```java
/**
 * 获取新字段数据
 * 对应 PDF 字段: newFieldKey
 */
public Map<String, Object> getNewFieldData() {
    HashMap<String, Object> result = new HashMap<>();

    // 实现数据获取逻辑
    result.put("newFieldKey", "字段值");

    return result;
}
```

### 2. 在数据库中配置方法映射

在 `contract_protocol_config` 表中插入配置:

```sql
INSERT INTO contract_protocol_config (
    form_id,
    form_key,
    form_field_key,
    form_field_name,
    deal_function,
    allow_blank,
    del_status
) VALUES (
    12345,                  -- 合同模板 ID
    'personal_contract',    -- 模板 key
    'newFieldKey',          -- PDF 字段 key
    '新字段名称',            -- 字段中文名
    'getNewFieldData',      -- 方法名(必须与代码一致)
    0,                      -- 不允许为空
    0                       -- 未删除
);
```

### 3. 验证配置

```java
// 协议平台会根据 formId 查询配置
List<ContractProtocolConfig> configs =
    contractProtocolConfigService.getContractProtocolConfig(formKey, formId);

// 获取所有 dealFunction
Set<String> dealFunctions = configs.stream()
    .map(ContractProtocolConfig::getDealFunction)
    .filter(StringUtils::isNotBlank)
    .collect(Collectors.toSet());

// dealFunctions 应该包含 "getNewFieldData"
```

---

## 常见问题

### Q1: 为什么方法不能改名?

**A**: 方法名配置在数据库中,通过反射调用。改名后:
1. 反射找不到方法,抛出 `NoSuchMethodException`
2. PDF 生成失败
3. 需要同步更新数据库配置,容易遗漏

### Q2: 如何查看某个 PDF 字段的数据来源?

**A**:
1. 根据 `formId` 查询 `contract_protocol_config` 表
2. 找到对应 `form_field_key` 的记录
3. 查看 `deal_function` 字段,即方法名
4. 在 `ContractPdfBuildService` 中找到该方法
5. 查看 `result.put(key, value)` 中 value 的来源

### Q3: 一个方法可以返回多个字段吗?

**A**: 可以。一个方法返回的 Map 可以包含多个 key-value:

```java
public Map<String, Object> getStructureInfo() {
    HashMap<String, Object> result = new HashMap<>();
    result.put("structure", "...");      // 字段1
    result.put("roomCnt", "...");        // 字段2
    result.put("parlorCnt", "...");      // 字段3
    // ...可以继续添加更多字段
    return result;
}
```

数据库中可以配置多条记录,都指向同一个 `deal_function`:

```
form_field_key | deal_function
---------------|---------------
structure      | getStructureInfo
roomCnt        | getStructureInfo
parlorCnt      | getStructureInfo
```

### Q4: 方法抛出异常会怎样?

**A**:
- 反射调用时会捕获异常
- 日志记录: `pdf生成时，调用方法异常,方法名：{}`
- 抛出 `NrsBusinessException`,导致 PDF 生成失败
- 因此方法内部必须做好异常处理和空指针防护

### Q5: 如何调试反射调用?

**A**:
1. 在 `ContractPdfCreateService.buildFormData()` 打断点
2. 查看 `dealFunctions` 集合,确认包含你的方法名
3. 进入反射调用,查看 `invokeResult`
4. 检查日志: `pdf生成时，调用方法{}返回结果为：{}`

---

## 反模式 (❌ 不要这样做)

### ❌ 不要修改方法名

```java
// ❌ 错误: 重命名方法
public Map<String, Object> getContractNumber() {  // 原名: getContractNo
    // 反射调用会失败: NoSuchMethodException
}
```

### ❌ 不要删除看似未使用的方法

```java
// ❌ 错误: 删除方法
// public Map<String, Object> getOldField() {
//     // 这个方法虽然代码里没有直接调用,但数据库配置了反射调用
// }
```

### ❌ 不要添加参数

```java
// ❌ 错误: 添加参数
public Map<String, Object> getContractNo(String param) {
    // 反射调用传 null,会找不到这个方法签名
}
```

### ❌ 不要直接返回 null

```java
// ❌ 错误: 返回 null
public Map<String, Object> getContractNo() {
    return null;  // 会导致 formData.putAll(null) 异常
}

// ✅ 正确: 返回空 Map
public Map<String, Object> getContractNo() {
    return new HashMap<>();
}
```

### ❌ 不要忽略空指针风险

```java
// ❌ 错误: 直接调用可能为 null 的对象
public Map<String, Object> getPromiseInfo() {
    HashMap<String, Object> result = new HashMap<>();
    result.put("status", contractReq.getPromiseInfo().getStatus());  // NPE 风险
    return result;
}

// ✅ 正确: 使用 Optional
public Map<String, Object> getPromiseInfo() {
    HashMap<String, Object> result = new HashMap<>();
    String status = Optional.ofNullable(contractReq.getPromiseInfo())
        .map(PromiseInfo::getStatus)
        .orElse("");
    result.put("status", status);
    return result;
}
```

---

## 特殊业务逻辑

### 场景一: PDF 生成模式判断

**业务背景**:

整装 2.5 场景中,合同 PDF 生成有两种模式:

1. **无版式模式 (UNFORMATTED)**: 系统自行生成 PDF
2. **有版式模式 (FORMATTED)**: 协议平台生成 PDF

两种模式的数据处理方式不同。

---

#### 模式说明

**枚举定义**: `PdfGenerationModeEnum`

| 枚举值 | Code | 说明 |
|--------|------|------|
| `FORMATTED` | 1 | 有版式 - 协议平台生成 |
| `UNFORMATTED` | 2 | 无版式 - 系统生成 |

**存储位置**: `Contract.pdfGenerationMode` 字段

---

#### 两种模式的流程差异

**无版式模式 (UNFORMATTED)**:

```
1. 调用协议平台生成纯文本 PDF (不包含图纸/报价单)
2. 系统查询图纸/报价单 → 生成 PDF → 追加到合同 PDF
3. 原因: 大文件在协议平台可能失败,系统生成可以压缩
```

**有版式模式 (FORMATTED)**:

```
1. 通过反射调用方法获取图纸/报价单数据
2. 将所有数据传输给协议平台
3. 协议平台生成完整 PDF (包含图纸/报价单)
```

---

#### 代码模式

**在方法中判断模式,决定是否跳过数据处理**:

```java
public Map<String, Object> getDrawingData() {
    HashMap<String, Object> result = new HashMap<>();

    // 判断 PDF 生成模式
    if (PdfGenerationModeEnum.UNFORMATTED.getCode().equals(
        ContractContextHandler.getContext().getContract().getPdfGenerationMode())) {
        // 无版式模式: 系统自行处理图纸,不需要传给协议平台
        return result;  // 返回空 Map
    }

    // 有版式模式: 需要将图纸数据传给协议平台
    DrawingDTO drawingDTO = ContractContextHandler.getContext().getDrawingDTO();

    // 处理图纸数据...
    List<String> imageUrls = // 获取图纸图片 URL 列表

    // 转换为 PhotoInfo 格式
    String signDate = DateUtils.getDateStr(new Date());
    List<FormalPackageContractFreeformDTO.PhotoInfo> photos = imageUrls.stream()
        .map(src -> new FormalPackageContractFreeformDTO.PhotoInfo(src, signDate, false))
        .collect(Collectors.toList());

    if (CollectionUtils.isNotEmpty(photos)) {
        photos.get(photos.size() - 1).setSign(true);  // 最后一页盖章
    }

    result.put("drawingUrlV2", JsonUtil.toJsonString(photos));
    return result;
}
```

**关键点**:
- 无版式模式直接返回空 Map,跳过数据处理
- 有版式模式正常处理数据并返回
- 通过 `ContractContextHandler.getContext().getContract().getPdfGenerationMode()` 获取模式

---

### 场景二: 盖章页标记

**业务背景**:

合同 PDF 中的附件(图纸、报价单、细则等)需要标记哪些页面需要盖章。通常是在最后一页盖章。

---

#### PhotoInfo 数据结构

**类**: `FormalPackageContractFreeformDTO.PhotoInfo`

**字段**:
- `src`: 图片 URL
- `signDate`: 签署日期
- `sign`: 是否需要盖章 (true/false)

**用途**: 协议平台根据 `sign` 字段判断是否在该页添加电子印章

---

#### 代码模式

**标准流程**:

```java
public Map<String, Object> getMaterialForB() {
    HashMap<String, Object> result = new HashMap<>();

    // 1. 获取 PDF 文件 URL 列表
    List<String> materialForB = new ArrayList<>();
    // ... 业务逻辑获取文件列表

    // 2. 将 PDF 转换为图片 URL 列表
    List<String> imageUrls = new ArrayList<>();
    for (String fileUrl : materialForB) {
        imageUrls.addAll(pdfToImageService.pdf2ImagePublicParallel(fileUrl));
    }

    // 3. 转换为 PhotoInfo 格式 (默认 sign=false)
    String signDate = DateUtils.getDateStr(new Date());
    List<FormalPackageContractFreeformDTO.PhotoInfo> photos = imageUrls.stream()
        .map(src -> new FormalPackageContractFreeformDTO.PhotoInfo(src, signDate, false))
        .collect(Collectors.toList());

    // 4. 标记最后一页需要盖章
    if (CollectionUtil.isNotEmpty(photos)) {
        photos.get(photos.size() - 1).setSign(true);
    }

    // 5. 序列化为 JSON 字符串传给协议平台
    result.put("materialForB", JsonUtil.toJsonString(photos));
    return result;
}
```

**关键步骤**:

1. **创建 PhotoInfo 列表** - 所有页面初始 `sign=false`
2. **标记最后一页** - `photos.get(photos.size() - 1).setSign(true)`
3. **序列化为 JSON** - `JsonUtil.toJsonString(photos)`

---

#### 完整示例: getMaterialForB 方法

```java
/**
 * 获取 B 承担部分材料清单
 * 对应 PDF 字段: materialForB
 * 场景: 整装 2.5 B 或 BC 付款方式
 */
public Map<String, Object> getMaterialForB() {
    HashMap<String, Object> result = new HashMap<>();
    DrawingDTO.DeliverDrawingDTO drawingDTO = ContractContextHandler.getContext().getDrawingDTO();
    Byte contractType = ContractContextHandler.getContext().getContract().getType();
    Byte businessType = ContractContextHandler.getContext().getBusinessType();
    String projectOrderId = ContractContextHandler.getContractReq().getContractBaseInfo().getProjectOrderId();

    // 判断是否为 B 或 BC 付款方式
    boolean bOrBCPaymentType = commonBusinessService.isBOrBCPaymentType(projectOrderId);

    List<String> materialForB = new ArrayList<>();
    if (drawingDTO == null) {
        return result;
    }

    // 根据业务类型和合同类型筛选配置清单
    if (BusinessTypeEnum.GROUP_DECORATE.getCode().equals(businessType)) {
        if (ContractTypeEnum.PACKAGE_FORMAL.getCode().equals(contractType) && bOrBCPaymentType) {
            // 正签合同: 筛选基础套餐的配置清单
            List<String> list = drawingDTO.getDrawingDetailDTOList().stream()
                .filter(item -> ObjectUtil.equal(item.getEncodeType(), PlanAttachment.商品清单))
                .map(DrawingDTO.DrawingDetailDTO::getUrl)
                .collect(Collectors.toList());
            materialForB.addAll(list);
        } else if (ContractTypeEnum.PERSONAL.getCode().equals(contractType) && bOrBCPaymentType) {
            // 销售合同: 筛选定软电的配置清单
            List<String> list = drawingDTO.getDrawingDetailDTOList().stream()
                .filter(item -> ObjectUtil.equal(item.getEncodeType(), PlanAttachment.软装配置清单))
                .map(DrawingDTO.DrawingDetailDTO::getUrl)
                .collect(Collectors.toList());
            materialForB.addAll(list);
        }
    }

    // PDF 转图片
    List<String> imageUrls = new ArrayList<>();
    for (String fileUrl : materialForB) {
        imageUrls.addAll(pdfToImageService.pdf2ImagePublicParallel(fileUrl));
    }

    // 转换为 PhotoInfo 格式
    String signDate = DateUtils.getDateStr(new Date());
    List<FormalPackageContractFreeformDTO.PhotoInfo> photos = imageUrls.stream()
        .map(src -> new FormalPackageContractFreeformDTO.PhotoInfo(src, signDate, false))
        .collect(Collectors.toList());

    if (CollectionUtil.isNotEmpty(photos)) {
        // 设置最后一页盖章
        photos.get(photos.size() - 1).setSign(true);
    }

    result.put("materialForB", JsonUtil.toJsonString(photos));
    return result;
}
```

---

#### 常见应用场景

| 字段 | 说明 | 是否标记盖章 |
|------|------|-------------|
| `drawingUrlV2` | 施工图纸 | ✅ 最后一页 |
| `budgetUrlV2` | 报价单 | ✅ 最后一页 |
| `decorateRuleUrlV2` | 精装细则 | ✅ 最后一页 |
| `personalBudgetUrl` | 个性化报价 | ✅ 最后一页 |
| `materialForB` | B 承担材料清单 | ✅ 最后一页 |

**统一规则**: 附件的最后一页需要盖章,其他页不盖章

---

#### 注意事项

1. **空列表检查**: 必须先检查 `photos` 是否为空,避免 `IndexOutOfBoundsException`
   ```java
   if (CollectionUtil.isNotEmpty(photos)) {
       photos.get(photos.size() - 1).setSign(true);
   }
   ```

2. **JSON 序列化**: 协议平台接收的是 JSON 字符串,不是对象
   ```java
   result.put("fieldName", JsonUtil.toJsonString(photos));  // 正确
   result.put("fieldName", photos);  // 错误
   ```

3. **签署日期**: 使用当前日期,格式化为字符串
   ```java
   String signDate = DateUtils.getDateStr(new Date());
   ```

4. **初始值**: 创建 PhotoInfo 时,`sign` 默认为 `false`
   ```java
   new FormalPackageContractFreeformDTO.PhotoInfo(src, signDate, false)
   ```
