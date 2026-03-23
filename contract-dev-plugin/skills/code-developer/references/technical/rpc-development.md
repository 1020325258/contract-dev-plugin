---
name: rpc-development
description: RPC 调用开发规范,基于签约项目实际实现,包含 RpcHelper 使用、日志打印、异常处理等规范
---

# RPC 开发规范

## 适用场景
跨服务 RPC 调用时必须遵循的规范,包括调用报价领域、主订单领域、合同领域等远程服务。

---

## 核心工具类: RpcHelper

签约项目统一使用 `RpcHelper` 工具类来处理 RPC 调用,封装了统一的异常处理和日志记录。

**位置**: `com.ke.utopia.nrs.salesproject.rpc.utils.RpcHelper`

---

## 标准调用模式

### 模式一: 使用 RpcHelper.unwrap (推荐)

**适用场景**: 大部分 RPC 调用,返回 `ResultDTO<T>` 类型

```java
@Service
@Slf4j
public class SubOrderFeignService {

    @Resource
    private SubOrderQueryApi subOrderQueryApi;

    /**
     * 根据主订单号查询状态有效的子单
     */
    public List<SubOrderBaseInfoDTO> queryValidBaseInfoByHomeOrderNo(
            String projectOrderId, String billCode, String changeOrderId) {

        // 使用 RpcHelper.unwrap 统一处理
        List<SubOrderBaseInfoDTO> subOrderBaseInfos = RpcHelper.unwrap(
            () -> subOrderQueryApi.queryBaseInfoByHomeOrderNo(projectOrderId, billCode, changeOrderId),
            "根据主单号查询子单信息"  // API 名称,用于日志记录
        );

        // 后续业务处理
        return subOrderBaseInfos.stream()
            .filter(subOrderInfo -> !invalidStatus.contains(subOrderInfo.getStatus()))
            .collect(Collectors.toList());
    }
}
```

**RpcHelper.unwrap 的优势**:
- 自动解包 `ResultDTO`,返回 `data` 数据
- 自动检查 `ResultDTO.isSuccess()`,失败时抛出 `BizException`
- 统一记录异常日志,包含 API 名称和堆栈信息
- 无需手动编写 try-catch

---

### 模式二: 手动 try-catch (非核心数据降级场景)

**适用场景**: 非核心数据查询,需要降级处理,允许失败后返回默认值

```java
@Service
@Slf4j
public class PayAccountFeignService {

    @Resource
    PayAccountFeign payAccountFeign;

    /**
     * 获取实名认证url
     * 非核心数据,失败时返回 null
     */
    public AuthPrepareDTO getAuthUrl(String ucId, String bizCode, String client, String returnUrl) {
        AuthPrepareParam param = new AuthPrepareParam();
        param.setUcid(ucId);
        param.setUserType("Customer");
        param.setProduct("userAuth");
        param.setBizCode(bizCode);
        param.setClient(client);
        param.setReturnUrl(returnUrl);

        try {
            // 1. 调用前日志: 记录入参
            LOGGER.info("获取用户实名认证url入参:{}", param);

            // 2. RPC 调用
            UserPlatformResult<AuthPrepareDTO> result = payAccountFeign.getAuthUrl(param);

            // 3. 调用成功日志: 记录返回值
            LOGGER.info("获取用户实名认证url返回值:{}", result);

            return result.getData();

        } catch (Exception e) {
            // 4. 异常日志: 记录完整堆栈
            LOGGER.error("获取实名认证信息失败，入参:{},e:{}", param, e);
        }

        // 5. 降级返回 null
        return null;
    }
}
```

**关键点**:
- 调用前记录入参 (INFO)
- 调用成功记录返回值 (INFO)
- 异常时记录完整堆栈 (ERROR)
- 非核心数据允许返回 null 降级

---

## 日志打印规范

### 1. 使用 RpcHelper.unwrap 时的日志

RpcHelper 会自动记录异常日志,格式如下:

```
ERROR ==>>> API(根据主单号查询子单信息)调用异常:
```

**你需要做的**:
- 提供清晰的 API 名称描述
- 无需额外记录日志

### 2. 手动 try-catch 时的日志规范

#### 调用前日志 (INFO 级别)
```java
LOGGER.info("获取用户实名认证url入参:{}", param);
```

**要求**:
- 必须记录关键业务参数
- 使用占位符 `{}` 避免字符串拼接
- 避免记录敏感信息(手机号、身份证需脱敏)

#### 调用成功日志 (INFO 级别)
```java
LOGGER.info("获取用户实名认证url返回值:{}", result);
```

**要求**:
- 记录返回值或关键状态
- 可以记录完整对象,fastjson 会自动序列化

#### 调用失败日志 (ERROR 级别)
```java
LOGGER.error("获取实名认证信息失败，入参:{},e:{}", param, e);
```

**要求**:
- 必须记录完整异常堆栈 `e`
- 记录调用参数,便于问题重现
- 异常信息放在占位符 `{}` 中

---

## 异常处理规范

### 策略选择

| 场景 | 使用方式 | 异常处理 |
|------|---------|---------|
| **核心流程数据** | `RpcHelper.unwrap` | 抛出 `BizException`,中断流程 |
| **非核心数据** | 手动 try-catch | 返回 null/空列表,记录 ERROR 日志 |
| **可忽略的错误码** | `RpcHelper.unwrapWithoutResultCodeCheck` | 特定错误码返回 null |

### 核心流程示例 (使用 RpcHelper)

```java
/**
 * 获取子单信息 - 核心流程,失败必须抛异常
 */
public List<SubOrderDto> batchQuerySubOrderByNo(List<String> subOrderNos) {
    // RpcHelper 自动处理异常,失败时抛出 BizException
    return RpcHelper.unwrap(
        () -> orderQueryApi.batchQuerySubOrderByNo(
            OrderBatchQueryParam.builder().orderNos(subOrderNos).build()
        ),
        "批量查询子单信息"
    );
}
```

### 非核心数据降级示例

```java
/**
 * 获取附件列表 - 非核心数据,失败时降级返回空列表
 */
public List<AttachmentDTO> getAttachments(String contractCode) {
    try {
        LOGGER.info("开始获取附件列表, contractCode: {}", contractCode);

        List<AttachmentDTO> attachments = attachmentRpcService.getAttachments(contractCode);

        LOGGER.info("获取附件列表成功, contractCode: {}, count: {}",
            contractCode, attachments.size());

        return attachments;

    } catch (Exception e) {
        LOGGER.error("获取附件列表失败, contractCode: {}, 返回空列表", contractCode, e);
        return Collections.emptyList(); // 降级返回空列表
    }
}
```

---

## RpcHelper 高级用法

### 1. 带参数的调用

```java
public BillDetailDTO getBillDetail(String billCode) {
    return RpcHelper.unwrap(
        (code) -> quotationClient.getBillDetail(code),
        billCode,  // 参数
        "获取报价单详情"
    );
}
```

### 2. 懒加载缓存调用

**适用场景**: 同一个请求链路中可能多次调用相同接口

```java
public BillDetailDTO getBillDetailWithCache(String billCode) {
    return RpcHelper.lazyLoadUnwrap(
        () -> quotationClient.getBillDetail(billCode),
        "获取报价单详情",
        billCode  // 用于生成缓存 key
    );
}
```

**缓存机制**:
- 基于 traceId + apiName + 参数 MD5 生成缓存 key
- 缓存有效期 30 秒
- 只在同一个请求链路(traceId)内生效

### 3. 忽略特定错误码

**适用场景**: 某些错误码不应该抛异常,需要返回 null

```java
public ContractDTO getContract(String contractCode) {
    return RpcHelper.unwrapWithoutResultCodeCheck(
        () -> contractApi.getContract(contractCode),
        "获取合同信息",
        Arrays.asList(
            RpcResultCodeEnum.CONTRACT_NOT_FOUND,  // 合同不存在时返回 null
            RpcResultCodeEnum.CONTRACT_DELETED     // 合同已删除时返回 null
        )
    );
}
```

---

## 返回值校验规范

### 1. RpcHelper.unwrap 自动校验

RpcHelper 会自动进行以下校验:
- 返回值为 null → 抛出 `BizException`
- `ResultDTO.isSuccess() == false` → 抛出 `BizException`

### 2. 业务数据校验

**即使使用 RpcHelper,也需要对返回的业务数据进行校验**:

```java
public BillDetailDTO getBillDetail(String billCode) {
    // RpcHelper 保证返回值不为 null,且 ResultDTO.isSuccess() == true
    BillDetailDTO billDetail = RpcHelper.unwrap(
        () -> quotationClient.getBillDetail(billCode),
        "获取报价单详情"
    );

    // 但 data 可能为 null,需要业务校验
    if (billDetail == null) {
        LOGGER.warn("报价单不存在, billCode: {}", billCode);
        throw new NrsBusinessException("报价单不存在");
    }

    // 校验业务状态
    if (!BillStatusEnum.FORMAL.getCode().equals(billDetail.getStatus())) {
        LOGGER.warn("报价单状态不正确, billCode: {}, status: {}",
            billCode, billDetail.getStatus());
        throw new NrsBusinessException("报价单状态必须为正式版");
    }

    return billDetail;
}
```

---

## 完整示例

### 示例 1: 标准 RPC 调用 (使用 RpcHelper)

```java
@Service
@Slf4j
public class SubOrderFeignService {

    @Resource
    private SubOrderQueryApi subOrderQueryApi;

    /**
     * 根据主订单号查询状态有效的子单
     */
    public List<SubOrderBaseInfoDTO> queryValidBaseInfoByHomeOrderNo(
            String projectOrderId, String billCode, String changeOrderId) {

        // 使用 RpcHelper.unwrap 统一处理
        List<SubOrderBaseInfoDTO> subOrderBaseInfos = RpcHelper.unwrap(
            () -> subOrderQueryApi.queryBaseInfoByHomeOrderNo(projectOrderId, billCode, changeOrderId),
            "根据主单号查询子单信息"
        );

        // 过滤无效状态的子单
        return subOrderBaseInfos.stream()
            .filter(subOrderInfo -> !invalidStatus.contains(subOrderInfo.getStatus()))
            .collect(Collectors.toList());
    }

    /**
     * 获取变更中的子单
     */
    public Set<String> getChangingSubOrderNos(List<String> subOrderNos) {
        List<ItemChangeRecordDto> itemChangeRecords = RpcHelper.unwrap(
            () -> orderQueryApi.queryItemChangeRecordListBySubOrderNoList(subOrderNos),
            "查询子单变更明细"
        );

        return itemChangeRecords.stream()
            .filter(record -> record.getStatus() == ItemChangeStatusEnum.PROCESSING.getType())
            .map(ItemChangeRecordDto::getOrderNo)
            .collect(Collectors.toSet());
    }
}
```

### 示例 2: 降级处理 (手动 try-catch)

```java
@Service
@Slf4j
public class PayAccountFeignService {

    @Resource
    PayAccountFeign payAccountFeign;

    /**
     * 获取实名认证url - 非核心数据,失败时返回 null
     */
    public AuthPrepareDTO getAuthUrl(String ucId, String bizCode, String client, String returnUrl) {
        AuthPrepareParam param = new AuthPrepareParam();
        param.setUcid(ucId);
        param.setUserType("Customer");
        param.setProduct("userAuth");
        param.setBizCode(bizCode);
        param.setClient(client);
        param.setReturnUrl(returnUrl);

        try {
            LOGGER.info("获取用户实名认证url入参:{}", param);
            UserPlatformResult<AuthPrepareDTO> result = payAccountFeign.getAuthUrl(param);
            LOGGER.info("获取用户实名认证url返回值:{}", result);
            return result.getData();
        } catch (Exception e) {
            LOGGER.error("获取实名认证信息失败，入参:{},e:{}", param, e);
        }

        return null;
    }
}
```

---

## 常见问题

### Q1: 什么时候用 RpcHelper,什么时候用手动 try-catch?

**A**:
- **核心流程**: 使用 `RpcHelper.unwrap`,让异常向上抛出
- **非核心数据**: 使用手动 try-catch,捕获异常后降级返回默认值

### Q2: RpcHelper.unwrap 中的 API 名称怎么写?

**A**: 使用中文描述,简洁明了,例如:
- ✅ "根据主单号查询子单信息"
- ✅ "批量查询子单信息"
- ❌ "subOrderQueryApi.queryBaseInfoByHomeOrderNo"

### Q3: 手动 try-catch 时一定要记录入参和返回值吗?

**A**:
- 入参: **必须记录**,便于问题重现
- 返回值: 建议记录,但可以根据返回数据大小决定
- 异常: **必须记录完整堆栈**

### Q4: RpcHelper 已经记录了异常日志,还需要在业务代码中再记录吗?

**A**:
- RpcHelper 的日志是兜底策略,只包含 API 名称和堆栈
- 如果需要记录更多业务上下文(如订单号、合同号),应该在业务代码中 catch 后再记录
- 记录后需要重新抛出异常: `throw new NrsBusinessException(e.getMessage(), e)`

### Q5: 什么情况下使用 lazyLoadUnwrap?

**A**:
- 同一个请求链路中可能多次调用相同接口
- 接口响应数据变化不频繁(30 秒内可接受缓存)
- 注意: 不要用于写操作或实时性要求高的查询

---

## 反模式 (❌ 不要这样做)

### ❌ 不要吞掉异常

```java
// ❌ 错误: 捕获异常后不处理,也不抛出
try {
    result = rpcService.query();
} catch (Exception e) {
    // 什么都不做
}
```

### ❌ 不要在核心流程中降级返回 null

```java
// ❌ 错误: 核心数据失败应该抛异常,而不是返回 null
public ContractDTO getContract(String contractCode) {
    try {
        return contractRpcService.getContract(contractCode);
    } catch (Exception e) {
        LOGGER.error("获取合同失败", e);
        return null;  // 核心数据不应该降级
    }
}
```

### ❌ 不要重复包装异常

```java
// ❌ 错误: RpcHelper 已经抛出 BizException,不需要再包装
try {
    result = RpcHelper.unwrap(() -> api.query(), "查询");
} catch (Exception e) {
    throw new BizException(e.getMessage(), e);  // 多余
}
```

### ❌ 不要使用模糊的 API 名称

```java
// ❌ 错误: API 名称不清晰
RpcHelper.unwrap(() -> api.query(), "query");

// ✅ 正确: 使用清晰的中文描述
RpcHelper.unwrap(() -> api.query(), "根据订单号查询订单详情");
```
