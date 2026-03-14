# Maven 测试执行问题排查指南

## 问题概述

在 utopia-nrs-sales-project 多模块 Maven 项目中执行单元测试时，可能会遇到编译失败和依赖解析失败的问题。本文档记录了典型问题及解决方案。

## 问题场景

### 场景 1：编译失败导致测试无法执行

#### 问题表现

```bash
mvn test -Dtest=BudgetBillSplitHandlerV2Test -pl utopia-nrs-sales-project-start
```

执行结果：
```
[ERROR] Failed to execute goal on project utopia-nrs-sales-project-start:
Could not resolve dependencies for project com.ke.utopia.nrs.salesproject:utopia-nrs-sales-project-start:jar:4.3.11
[ERROR] dependency: com.ke.utopia.nrs.salesproject:utopia-nrs-sales-project-service:jar:4.3.11 (compile)
[ERROR] Could not find artifact com.ke.utopia.nrs.salesproject:utopia-nrs-sales-project-service:jar:4.3.11
```

#### 根本原因

1. **依赖模块未编译**：`utopia-nrs-sales-project-service` 模块没有被编译并安装到本地 Maven 仓库
2. **上游编译错误**：`utopia-nrs-sales-project-rpc` 模块存在编译错误，导致 service 模块无法编译
3. **Maven 本地缓存**：之前失败的构建被缓存，导致 Maven 不再尝试重新解析依赖

### 解决方案

#### 方案 1：完整重新编译（推荐）

```bash
cd /Users/zqy/work/project/nrs-sales-project
mvn clean install -DskipTests
```

#### 方案 2：仅编译特定模块及其依赖

```bash
# -pl 指定模块，-am 自动构建依赖模块
mvn clean install -DskipTests -pl utopia-nrs-sales-project-start -am
```

#### 方案 3：从失败模块继续

```bash
mvn clean install -DskipTests -rf :utopia-nrs-sales-project-rpc
```

### 场景 2：测试代码编译失败（枚举值不存在）

#### 问题表现

```
找不到符号：变量 COMMIT（位置：ContractStatusEnum）
```

#### 解决步骤

查看枚举类实际定义，使用正确的枚举值（如 `FINISH` 而非 `COMMIT`）。

### 场景 3：验证测试是否能运行

```bash
# 仅编译测试代码（不运行）
mvn test-compile -pl utopia-nrs-sales-project-start

# 运行特定测试类
mvn test -Dtest=YourTestClass -pl utopia-nrs-sales-project-start
```

## 模块编译顺序

```
utopia-nrs-sales-project (parent)
├── utopia-nrs-sales-project-base
├── utopia-nrs-sales-project-api       (depends on base)
├── utopia-nrs-sales-project-dao       (depends on base, api)
├── utopia-nrs-sales-project-rpc       (depends on base, api, dao)
├── utopia-nrs-sales-project-service   (depends on base, api, dao, rpc)
└── utopia-nrs-sales-project-start     (depends on all above)
```

rpc 模块编译失败会导致 service 和 start 均无法编译，必须按顺序解决。

## 快速参考

| 错误信息 | 解决方案 |
|---------|---------|
| Could not find artifact ...service:jar | `mvn clean install -DskipTests` |
| 找不到符号：变量 COMMIT | 查看枚举定义，使用正确枚举值 |
| BUILD FAILURE at rpc module | 检查具体错误，修复或临时注释 |
