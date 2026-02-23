---
name: scheduled-task-development
description: 定时任务开发规范,基于签约项目实际实现,使用链家调度框架 @LianjiaSchedule
---

# 定时任务开发规范

## 适用场景
需要定期执行的后台任务,如数据检查、状态同步、定时清理、预警通知等。

---

## 核心框架: @LianjiaSchedule

签约项目使用链家调度框架 `@LianjiaSchedule` 进行定时任务开发。

**核心注解**:
- `@LianjiaSchedule`: 类级别注解,标记为定时任务类
- `@Assignment`: 方法级别注解,定义具体的调度任务

---

## 标准开发模式

### 基础结构

```java
@LianjiaSchedule
@Slf4j
public class YourSchedule {

    @Resource
    private YourService yourService;

    @Assignment(key = "yourScheduleKey", cn = "任务中文名称")
    public AssignmentResult yourScheduleMethod(AssignmentContext context) {
        try {
            // 1. 任务开始日志
            LOGGER.info("yourScheduleKey start");

            // 2. 获取任务参数(可选)
            String param = context.getParam().getOrDefault("paramKey", "defaultValue");

            // 3. 执行业务逻辑
            // ...

            // 4. 返回成功结果
            return new AssignmentResult(ResultMode.EXECUTE_SUCCESS);

        } catch (Exception e) {
            // 5. 异常处理
            LOGGER.error("yourScheduleKey failed", e);
            return new AssignmentResult(ResultMode.EXECUTE_FAIL);
        }
    }
}
```

**关键要求**:
- 类必须添加 `@LianjiaSchedule` 注解
- 建议添加 `@Slf4j` 用于日志记录
- 方法签名固定: `AssignmentResult methodName(AssignmentContext context)`
- 必须返回 `AssignmentResult`,使用 `ResultMode.EXECUTE_SUCCESS` 或 `EXECUTE_FAIL`

---

## 常见任务类型

### 类型一: 状态同步任务

**场景**: 查询特定状态的数据,执行批量处理

**示例**: 合同自动发起 BPM 审核

```java
@LianjiaSchedule
@Slf4j
public class ApplyBpmSchedule {

    @Resource
    ContractService contractService;

    @Resource
    ContractBusinessService contractBusinessService;

    @Assignment(key = "ApplyBpmSchedule", cn = "合同审核脚本")
    public AssignmentResult fixApplyBpmAudit(AssignmentContext context) {
        // 1. 查询待处理数据
        List<Contract> contractList = contractService.getListByStatus(
            ContractStatusEnum.PENDING_SUBMIT_AUDIT.getCode()
        );

        // 2. 空数据快速返回
        if (contractList.isEmpty()) {
            return new AssignmentResult(ResultMode.EXECUTE_SUCCESS);
        }

        // 3. 批量处理
        for (Contract contract : contractList) {
            try {
                contractBusinessService.dealContractForBpm(contract.getContractCode());
            } catch (Exception ignored) {
                // 单条失败不影响其他数据处理
            }
        }

        return new AssignmentResult(ResultMode.EXECUTE_SUCCESS);
    }
}
```

**关键点**:
- 空数据检查,避免无效循环
- 使用 try-catch 包裹单条处理,单条失败不影响整体
- 批量处理时考虑性能,必要时分页处理

---

### 类型二: 数据检查/预警任务

**场景**: 检查数据异常情况并报警

**示例**: 异步盖章时间检查

```java
@LianjiaSchedule
@Slf4j
public class AsyncSignTimeCheckSchedule {

    @Resource
    private ContractService contractService;

    @Resource
    private ContractRedisRepoService contractRedisService;

    @Resource
    private ContractApolloConfig contractApolloConfig;

    @Assignment(key = "asyncSignTimeCheckSchedule", cn = "异步盖章时间检查")
    public AssignmentResult asyncSignTimeCheck(AssignmentContext context) {
        // 1. 查询待检查数据
        List<Contract> contractList = contractService.getListByStatus(
            ContractStatusEnum.PENDING_COMPANY_SIGN.getCode()
        );

        if (contractList.isEmpty()) {
            return new AssignmentResult(ResultMode.EXECUTE_SUCCESS);
        }

        // 2. 逐条检查
        for (Contract contract : contractList) {
            CompanySealAsyncResultDTO resultDTO =
                contractRedisService.getCompanySealResult(contract.getContractCode());

            if (resultDTO == null) {
                continue;
            }

            // 3. 计算时间差
            long threshold = 60 * 1000 * contractApolloConfig.getAsyncSignTimeCheckValue();
            long elapsed = System.currentTimeMillis() - resultDTO.getApplySealTime();

            // 4. 超时报警
            if (elapsed > threshold) {
                LOGGER.error("异步盖章时间检查,时间过长还未收到盖章回调,合同信息:{}",
                    JSON.toJSONString(contract));
            }
        }

        return new AssignmentResult(ResultMode.EXECUTE_SUCCESS);
    }
}
```

**关键点**:
- 使用配置化的阈值(从 Apollo 或 context 参数获取)
- 异常情况使用 ERROR 级别日志记录
- 记录完整的业务数据便于排查

---

### 类型三: 数据核对任务

**场景**: 核对数据一致性

**示例**: 新旧表合同字段数据核对

```java
@LianjiaSchedule
@Slf4j
public class ContractFieldCheckSchedule {

    @Resource
    private ContractMapper contractMapper;

    @Resource
    private ContactFieldDealDataService contactFieldDealDataService;

    @Assignment(key = "contractFieldCheckSchedule", cn = "新旧表合同字段数据核对定时任务")
    public AssignmentResult contractFieldCheckSchedule(AssignmentContext context) {
        // 1. 获取任务参数
        long fromCheckId = Long.parseLong(
            context.getParam().getOrDefault("fromCheckId", "711418")
        );

        // 2. 计算检查范围
        long checkStartId = getCheckStartId(fromCheckId);
        long checkEndId = getCheckEndId(fromCheckId);

        LOGGER.info("合同字段数据核对定时任务，起始ID: {}, 结束ID: {}",
            checkStartId, checkEndId);

        // 3. 执行核对
        contactFieldDealDataService.checkDataConsistencyByIdRange(
            Integer.valueOf(String.valueOf(checkStartId)),
            Integer.valueOf(String.valueOf(checkEndId))
        );

        return new AssignmentResult(ResultMode.EXECUTE_SUCCESS);
    }

    /**
     * 获取检查起始ID
     */
    public long getCheckStartId(long fromCheckId) {
        Instant oneDayAgo = Instant.now().minus(1, ChronoUnit.DAYS);
        Date date = Date.from(oneDayAgo);

        Example example = new Example(Contract.class);
        example.orderBy("id").asc();
        Example.Criteria criteria = example.createCriteria()
            .andGreaterThanOrEqualTo("id", fromCheckId)
            .andGreaterThan(Contract.Fields.ctime, date)
            .andEqualTo("delStatus", CommonEnum.NO.getCode());

        RowBounds rowBounds = new RowBounds(0, 1);
        List<Contract> result = contractMapper.selectByExampleAndRowBounds(example, rowBounds);

        if (result != null && !result.isEmpty()) {
            return result.get(0).getId();
        }
        return fromCheckId;
    }
}
```

**关键点**:
- 支持通过参数控制检查范围
- 记录检查范围的开始和结束标识
- 使用分页查询避免一次加载大量数据

---

### 类型四: 统计预警任务

**场景**: 统计数据并根据阈值预警

**示例**: 隐私数据访问预警

```java
@LianjiaSchedule
@Slf4j
@Service
public class PrivacyAccessWarnSchedule {

    @Resource
    private SensitiveInformationAccessRecordService recordService;

    @Resource
    private PrivacyCommonService privacyCommonService;

    @Resource
    private ContractApolloConfig contractApolloConfig;

    @Assignment(key = "privacyAccessWarnSchedule", cn = "隐私数据访问预警脚本")
    public AssignmentResult privacyAccessWarnSchedule(AssignmentContext context) {
        LOGGER.info("privacyAccessWarnSchedule start");

        // 1. 获取可配置参数
        int time = Integer.parseInt(context.getParam().getOrDefault("time", "100"));
        Integer count = Integer.valueOf(context.getParam().getOrDefault("count", "10"));
        int range = Integer.parseInt(context.getParam().getOrDefault("range", "2"));

        // 2. 按时间段循环检查
        for (int i = 0; i < range; i++) {
            long currentTime = System.currentTimeMillis();

            // 3. 计算时间范围
            SimpleDateFormat dateFormat = new SimpleDateFormat("yyyy-MM-dd HH:mm:ss");
            String startTime = dateFormat.format(
                new Date(currentTime - (long) (i + 1) * time * 60 * 1000)
            );
            String endTime = dateFormat.format(
                new Date(currentTime - (long) i * time * 60 * 1000)
            );

            // 4. 查询访问记录
            List<SensitiveInformationAccessRecord> records =
                recordService.selectWarnRecord(startTime, endTime);

            // 5. 统计访问次数
            Map<String, Integer> viewContractCountMap = new HashMap<>();
            Map<String, Integer> copyPhoneCountMap = new HashMap<>();
            Map<String, String> ucidNameMap = new HashMap<>();

            for (SensitiveInformationAccessRecord record : records) {
                String ucid = record.getOperatorUcid();
                String operatorName = record.getOperatorName();
                ucidNameMap.put(ucid, operatorName);

                // 按操作类型统计
                if (PrivacyOperateTypeEnum.VIEW_CONTRACT_PDF.getCode()
                    .equals(record.getOperationType())) {
                    viewContractCountMap.put(ucid,
                        viewContractCountMap.getOrDefault(ucid, 0) + 1);
                }
            }

            // 6. 超过阈值则预警
            for (Map.Entry<String, Integer> entry : viewContractCountMap.entrySet()) {
                if (entry.getValue() > count) {
                    String ucid = entry.getKey();
                    String operatorName = ucidNameMap.get(ucid);

                    // 白名单过滤
                    if (!contractApolloConfig.getWarnWhiteList().contains(ucid)) {
                        String warnContent = String.format(
                            "【高频预览合同】「%s%s」，近%s分钟预览合同数%s份",
                            operatorName, ucid, time, entry.getValue()
                        );
                        privacyCommonService.overFrequencyWarn(ucid, operatorName, warnContent);
                    }
                }
            }
        }

        return new AssignmentResult(ResultMode.EXECUTE_SUCCESS);
    }
}
```

**关键点**:
- 支持多个可配置参数(时间窗口、阈值、范围)
- 使用 Map 进行分组统计
- 支持白名单机制避免误报
- 预警内容包含关键业务信息

---

## 日志规范

### 1. 任务开始日志 (INFO)

```java
LOGGER.info("yourScheduleKey start");
```

### 2. 关键参数日志 (INFO)

```java
LOGGER.info("合同字段数据核对定时任务，起始ID: {}, 结束ID: {}", checkStartId, checkEndId);
```

### 3. 异常情况日志 (ERROR)

```java
LOGGER.error("异步盖章时间检查,时间过长还未收到盖章回调,合同信息:{}",
    JSON.toJSONString(contract));
```

### 4. 任务失败日志 (ERROR)

```java
LOGGER.error("yourScheduleKey failed", e);
```

**要求**:
- 任务开始必须记录日志
- 记录关键业务参数(ID 范围、数据量等)
- 异常必须记录完整堆栈
- 预警信息使用 ERROR 级别

---

## 参数配置规范

### 通过 AssignmentContext 获取参数

```java
@Assignment(key = "yourSchedule", cn = "任务名称")
public AssignmentResult yourSchedule(AssignmentContext context) {
    // 获取参数,支持默认值
    String param1 = context.getParam().getOrDefault("param1", "defaultValue");
    int param2 = Integer.parseInt(context.getParam().getOrDefault("param2", "100"));

    // 使用参数...
}
```

**常见参数类型**:
- `time`: 时间窗口(分钟)
- `count`: 阈值次数
- `range`: 检查范围
- `fromCheckId`: 起始 ID
- `batchSize`: 批次大小

---

## 异常处理规范

### 原则

1. **整体任务不能因单条数据失败而中断**
2. **异常必须记录日志**
3. **根据场景决定是否返回失败**

### 模式一: 单条失败不影响整体

```java
for (Contract contract : contractList) {
    try {
        // 处理单条数据
        contractBusinessService.dealContractForBpm(contract.getContractCode());
    } catch (Exception ignored) {
        // 单条失败不影响其他数据
        // 注意: 这里吞掉异常是有业务含义的
    }
}
```

### 模式二: 记录异常但继续执行

```java
for (Contract contract : contractList) {
    try {
        // 处理单条数据
    } catch (Exception e) {
        LOGGER.error("处理合同失败, contractCode: {}", contract.getContractCode(), e);
        // 继续处理下一条
    }
}
```

### 模式三: 关键异常终止任务

```java
@Assignment(key = "criticalSchedule", cn = "关键任务")
public AssignmentResult criticalSchedule(AssignmentContext context) {
    try {
        // 关键业务逻辑
        return new AssignmentResult(ResultMode.EXECUTE_SUCCESS);
    } catch (Exception e) {
        LOGGER.error("criticalSchedule failed", e);
        return new AssignmentResult(ResultMode.EXECUTE_FAIL);
    }
}
```

---

## 性能优化建议

### 1. 分页处理大数据量

```java
int pageSize = 100;
int pageNo = 0;

while (true) {
    List<Contract> contractList = contractService.getByPage(pageNo, pageSize);
    if (contractList.isEmpty()) {
        break;
    }

    // 处理当前页数据
    for (Contract contract : contractList) {
        // ...
    }

    pageNo++;
}
```

### 2. 使用 RowBounds 限制查询结果

```java
RowBounds rowBounds = new RowBounds(0, 1);  // 只查询第一条
List<Contract> result = contractMapper.selectByExampleAndRowBounds(example, rowBounds);
```

### 3. 避免一次性加载大量数据

```java
// ❌ 错误: 一次性查询所有数据
List<Contract> allContracts = contractService.selectAll();

// ✅ 正确: 按条件分批查询
List<Contract> contracts = contractService.getListByStatus(status);
```

### 4. 使用配置控制执行范围

```java
// 通过参数控制只处理最近 N 天的数据
Instant oneDayAgo = Instant.now().minus(1, ChronoUnit.DAYS);
Date date = Date.from(oneDayAgo);
```

---

## 完整示例

```java
@LianjiaSchedule
@Slf4j
public class ContractCleanupSchedule {

    @Resource
    private ContractService contractService;

    @Resource
    private ContractBusinessService contractBusinessService;

    @Assignment(key = "contractCleanupSchedule", cn = "合同数据清理任务")
    public AssignmentResult contractCleanup(AssignmentContext context) {
        // 1. 任务开始日志
        LOGGER.info("contractCleanupSchedule start");

        try {
            // 2. 获取可配置参数
            int daysAgo = Integer.parseInt(
                context.getParam().getOrDefault("daysAgo", "30")
            );
            int batchSize = Integer.parseInt(
                context.getParam().getOrDefault("batchSize", "100")
            );

            // 3. 计算时间范围
            Instant cutoffTime = Instant.now().minus(daysAgo, ChronoUnit.DAYS);
            Date cutoffDate = Date.from(cutoffTime);

            LOGGER.info("开始清理 {} 天前的数据, 批次大小: {}", daysAgo, batchSize);

            // 4. 分页查询处理
            int pageNo = 0;
            int totalCleaned = 0;

            while (true) {
                List<Contract> contractList = contractService.getExpiredContracts(
                    cutoffDate, pageNo, batchSize
                );

                if (contractList.isEmpty()) {
                    break;
                }

                // 5. 批量处理
                for (Contract contract : contractList) {
                    try {
                        contractBusinessService.cleanupContract(contract.getContractCode());
                        totalCleaned++;
                    } catch (Exception e) {
                        LOGGER.error("清理合同失败, contractCode: {}",
                            contract.getContractCode(), e);
                        // 单条失败不影响整体
                    }
                }

                pageNo++;
            }

            // 6. 记录结果
            LOGGER.info("contractCleanupSchedule completed, 共清理: {} 条", totalCleaned);

            return new AssignmentResult(ResultMode.EXECUTE_SUCCESS);

        } catch (Exception e) {
            LOGGER.error("contractCleanupSchedule failed", e);
            return new AssignmentResult(ResultMode.EXECUTE_FAIL);
        }
    }
}
```

---

## 常见问题

### Q1: 什么时候返回 EXECUTE_FAIL?

**A**:
- 任务整体失败,无法继续执行
- 关键数据处理失败
- 大部分情况下,即使部分数据失败,也应返回 EXECUTE_SUCCESS

### Q2: 是否需要加分布式锁?

**A**:
- 链家调度框架已经保证同一任务不会并发执行
- 通常不需要额外的分布式锁
- 如果任务中有特殊并发场景,可以使用 `LockService`

### Q3: 如何避免任务执行时间过长?

**A**:
- 使用分页处理,每页数据量控制在 100-500 条
- 通过参数控制处理范围(时间、ID 范围)
- 避免在任务中执行耗时的同步 RPC 调用
- 考虑将大任务拆分为多个小任务

### Q4: 异常是否需要都记录日志?

**A**:
- 预期内的异常(如数据不存在)可以不记录或使用 WARN 级别
- 非预期异常必须记录 ERROR 日志和完整堆栈
- 单条数据失败根据业务重要性决定是否记录

---

## 反模式 (❌ 不要这样做)

### ❌ 不要一次性加载大量数据

```java
// ❌ 错误: 查询所有合同
List<Contract> allContracts = contractService.selectAll();
```

### ❌ 不要吞掉所有异常不记录

```java
// ❌ 错误: 完全忽略异常
try {
    // ...
} catch (Exception e) {
    // 什么都不做
}
```

### ❌ 不要在任务中执行大量同步 RPC

```java
// ❌ 错误: 循环中执行 RPC 调用
for (Contract contract : contractList) {
    // 每次都调用 RPC,性能差
    UserDTO user = userRpcService.getUser(contract.getUserId());
}

// ✅ 正确: 批量查询
List<String> userIds = contractList.stream()
    .map(Contract::getUserId)
    .collect(Collectors.toList());
Map<String, UserDTO> userMap = userRpcService.batchGetUsers(userIds);
```

### ❌ 不要使用固定的硬编码参数

```java
// ❌ 错误: 硬编码天数
int daysAgo = 30;

// ✅ 正确: 从参数获取
int daysAgo = Integer.parseInt(context.getParam().getOrDefault("daysAgo", "30"));
```
