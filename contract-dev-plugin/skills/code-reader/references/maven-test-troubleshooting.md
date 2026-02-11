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

#### 具体编译错误

```
[ERROR] /Users/zqy/work/project/nrs-sales-project/utopia-nrs-sales-project-rpc/src/main/java/com/ke/utopia/nrs/salesproject/rpc/fund/PayServiceRpc.java:[741,46]
找不到符号
  符号:   类 TerminateOrderPayVoucher
  位置: 类 com.ke.utopia.nrs.salesproject.rpc.fund.PayServiceRpc
```

### 解决方案

#### 方案 1：完整重新编译（推荐）

1. **清理项目并重新编译所有依赖模块**

```bash
cd /Users/zqy/work/project/nrs-sales-project
mvn clean install -DskipTests
```

这会：
- 清理所有 target 目录
- 编译所有模块
- 将所有模块安装到本地 Maven 仓库 (`~/.m2/repository`)
- 跳过测试执行，加快编译速度

2. **如果编译失败，检查具体错误模块**

根据 Reactor Summary 定位失败模块：
```
[INFO] Reactor Summary for utopia-nrs-sales-project 4.3.11:
[INFO]
[INFO] utopia-nrs-sales-project ........................... SUCCESS [  2.411 s]
[INFO] utopia-nrs-sales-project-base ...................... SUCCESS [ 31.867 s]
[INFO] utopia-nrs-sales-project-api ....................... SUCCESS [ 10.570 s]
[INFO] utopia-nrs-sales-project-dao ....................... SUCCESS [  8.247 s]
[INFO] utopia-nrs-sales-project-rpc ....................... FAILURE [  8.747 s]  ← 这里失败
```

3. **解决编译错误**

- 检查缺失的类定义
- 查看是否有其他分支引入的不兼容代码
- 必要时临时注释掉有问题的代码（记得添加 TODO 注释）

#### 方案 2：仅编译特定模块及其依赖

如果只想测试某个模块，可以仅编译该模块及其依赖：

```bash
# -pl 指定模块，-am 自动构建依赖模块
mvn clean install -DskipTests -pl utopia-nrs-sales-project-start -am
```

这会编译：
- utopia-nrs-sales-project-base
- utopia-nrs-sales-project-api
- utopia-nrs-sales-project-dao
- utopia-nrs-sales-project-rpc
- utopia-nrs-sales-project-service
- utopia-nrs-sales-project-start

#### 方案 3：清除 Maven 缓存

如果遇到缓存问题，清除特定 artifact 的本地缓存：

```bash
rm -rf ~/.m2/repository/com/ke/utopia/nrs/salesproject/
mvn clean install -DskipTests
```

### 场景 2：测试代码编译失败

#### 问题表现

```
[ERROR] /Users/zqy/work/project/nrs-sales-project/utopia-nrs-sales-project-start/src/test/java/com/ke/utopia/nrs/salesproject/service/contract/handler/BudgetBillSplitHandlerV2Test.java:[127,63]
找不到符号
  符号:   变量 COMMIT
  位置: 类 com.ke.utopia.nrs.salesproject.enums.contract.ContractStatusEnum
```

#### 根本原因

测试代码使用了不存在的枚举值。需要查看枚举类的实际定义。

#### 解决步骤

1. **查找枚举类定义**

```bash
find . -name "ContractStatusEnum.java" -type f
```

2. **查看枚举值**

```bash
grep -A 20 "public enum ContractStatusEnum" ./utopia-nrs-sales-project-base/src/main/java/com/ke/utopia/nrs/salesproject/enums/contract/ContractStatusEnum.java
```

常见的合同状态枚举：
```java
DRAFT(1, "起草中"),
PENDING_USER_CONFIRM(2, "待确认"),
USER_CONFIRMED(3, "已确认"),
PENDING_USER_SIGN(4, "待签署"),
PENDING_SUBMIT_AUDIT(5, "待提交审核"),
AUDITING(6, "审核中"),
PENDING_COMPANY_SIGN(7, "待盖公司章"),
FINISH(8, "已签署"),  // ← 注意是 FINISH 不是 COMMIT
CANCEL(9, "已取消"),
AUDIT_REJECT(10, "已驳回"),
```

3. **修正测试代码**

将错误的枚举值替换为正确的：
```bash
# 批量替换
sed -i '' 's/ContractStatusEnum.COMMIT/ContractStatusEnum.FINISH/g' BudgetBillSplitHandlerV2Test.java
```

或使用 Edit 工具进行精确替换。

### 场景 3：验证测试是否能运行

#### 仅编译测试代码（不运行）

```bash
mvn test-compile -pl utopia-nrs-sales-project-start
```

这会：
- 编译主代码（如果需要）
- 编译测试代码
- 不执行测试

成功输出：
```
[INFO] --- compiler:3.8.1:testCompile (default-testCompile) @ utopia-nrs-sales-project-start ---
[INFO] Changes detected - recompiling the module!
[INFO] Compiling 63 source files to /Users/zqy/work/project/nrs-sales-project/utopia-nrs-sales-project-start/target/test-classes
[INFO] ------------------------------------------------------------------------
[INFO] BUILD SUCCESS
```

#### 运行特定测试类

```bash
mvn test -Dtest=BudgetBillSplitHandlerV2Test -pl utopia-nrs-sales-project-start
```

成功输出：
```
[INFO] -------------------------------------------------------
[INFO]  T E S T S
[INFO] -------------------------------------------------------
[INFO] Running com.ke.utopia.nrs.salesproject.service.contract.handler.BudgetBillSplitHandlerV2Test
[INFO] Tests run: 5, Failures: 0, Errors: 0, Skipped: 0, Time elapsed: 0.546 s
[INFO] ------------------------------------------------------------------------
[INFO] BUILD SUCCESS
```

## 最佳实践

### 1. 测试驱动开发流程

```bash
# 步骤 1：确保项目能编译
mvn clean install -DskipTests

# 步骤 2：编写测试代码
# 创建 *Test.java 文件，使用 Mockito 等框架

# 步骤 3：编译测试代码
mvn test-compile -pl utopia-nrs-sales-project-start

# 步骤 4：运行测试
mvn test -Dtest=YourTest -pl utopia-nrs-sales-project-start

# 步骤 5：修改代码，重新测试
# 修改业务代码后，重新编译 service 模块
mvn clean install -DskipTests -pl utopia-nrs-sales-project-service
mvn test -Dtest=YourTest -pl utopia-nrs-sales-project-start
```

### 2. 快速反馈循环

**如果只修改了测试代码：**
```bash
mvn test-compile test -Dtest=YourTest -pl utopia-nrs-sales-project-start
```

**如果修改了 service 模块代码：**
```bash
# 重新编译 service 模块
mvn clean install -DskipTests -pl utopia-nrs-sales-project-service

# 运行测试
mvn test -Dtest=YourTest -pl utopia-nrs-sales-project-start
```

### 3. 处理持续编译错误

如果某个模块一直编译失败（如 rpc 模块的 TerminateOrderPayVoucher 问题）：

1. **评估影响范围**
   ```bash
   # 查找哪些文件引用了问题代码
   grep -r "TerminateOrderPayVoucher" utopia-nrs-sales-project-service/src/
   ```

2. **临时隔离问题**
   - 如果问题代码不影响当前开发，可以临时注释
   - 添加清晰的 TODO 注释说明原因
   - 完成开发后记得恢复

3. **检查分支差异**
   ```bash
   # 查看是否其他分支引入的问题
   git log --oneline --all --grep="TerminateOrderPayVoucher"
   git blame path/to/file.java
   ```

### 4. 理解 Maven Reactor

Maven 多模块项目的编译顺序由模块依赖关系决定：

```
utopia-nrs-sales-project (parent)
├── utopia-nrs-sales-project-base
├── utopia-nrs-sales-project-api (depends on base)
├── utopia-nrs-sales-project-dao (depends on base, api)
├── utopia-nrs-sales-project-rpc (depends on base, api, dao)
├── utopia-nrs-sales-project-service (depends on base, api, dao, rpc)
└── utopia-nrs-sales-project-start (depends on all above)
```

**重要规则：**
- 如果 rpc 模块编译失败，service 和 start 都无法编译
- 必须按顺序解决编译问题
- 使用 `-rf` 参数可以从失败的模块继续：
  ```bash
  mvn clean install -DskipTests -rf :utopia-nrs-sales-project-rpc
  ```

## 常见错误速查表

| 错误信息 | 原因 | 解决方案 |
|---------|------|---------|
| Could not find artifact ...service:jar:4.3.11 | service 模块未编译到本地仓库 | `mvn clean install -DskipTests` |
| 找不到符号：类 XXX | 缺少类定义或导入错误 | 检查 import，查找类定义 |
| 找不到符号：变量 COMMIT | 枚举值不存在 | 查看枚举定义，使用正确的枚举值 |
| BUILD FAILURE at rpc module | rpc 模块编译错误 | 检查具体错误，修复或临时注释 |
| Tests run: X, Failures: Y | 测试失败 | 检查测试日志，修复业务逻辑或测试代码 |

## 调试技巧

### 1. 查看详细编译信息

```bash
mvn clean install -DskipTests -X  # -X 显示 Debug 日志
```

### 2. 仅检查依赖关系

```bash
mvn dependency:tree -pl utopia-nrs-sales-project-start
```

### 3. 查看有效 POM

```bash
mvn help:effective-pom -pl utopia-nrs-sales-project-start
```

### 4. 验证本地仓库

```bash
ls -la ~/.m2/repository/com/ke/utopia/nrs/salesproject/
```

应该看到所有模块的 jar 文件。

## 总结

在 Maven 多模块项目中执行测试的关键点：

1. **确保依赖模块已编译并安装到本地仓库**
2. **从根本原因解决编译错误，不要跳过失败的模块**
3. **测试代码要使用正确的枚举值和类定义**
4. **理解 Maven Reactor 的构建顺序**
5. **遇到问题时，先尝试 `mvn clean install -DskipTests` 重新编译**

遵循这些原则，可以快速定位和解决测试执行问题，提高开发效率。
