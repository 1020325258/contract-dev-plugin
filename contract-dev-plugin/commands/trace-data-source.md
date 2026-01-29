---
description: 追踪指定变量或方法的来源，分析它从哪里获取、如何传递到当前位置。
argument-hint: "[变量名或方法名称]"
allowed-tools: Read, Grep, Glob, Bash(git log:*), Bash(git show:*)
---

## 任务目标

追踪指定数据的来源，回答"这个数据从哪里来？"

## 输入信息

### 用户指定的目标

- **如果用户提供了变量名**：追踪该变量的数据来源
  - 代码导航：
    - ContractPdfBuildService：封装了传递给协议平台变量的所有方法。


## 执行步骤
### 1. 收集前置信息


### 1. 定位目标数据

根据用户输入的变量名，确定对应的代码位置。


```bash
# 如果提供了变量名，在相关文件中搜索
grep -rn "variableName" src/

# 如果提供了文件和行号，直接读取
# (使用 Read 工具)
```

### 2. 向后追踪来源

从目标位置开始，逆向追踪数据流：

**步骤 A**：找到变量的赋值语句
```bash
# 搜索赋值操作
grep -n "variableName =" file.java
```

**步骤 B**：分析赋值右侧的来源
- 如果是方法调用：追踪该方法的返回值
- 如果是属性访问：追踪对象的来源
- 如果是参数：说明来自调用方
- 如果是计算表达式：追踪表达式中的每个变量

**步骤 C**：递归追踪直到原始来源
- 方法参数 → 调用方传入
- 数据库查询 → Repository/Mapper 方法
- 配置读取 → 配置文件或常量
- API 调用 → 外部服务
- 字面量 → 代码中直接定义

### 3. 记录传递路径

记录数据从原始来源到目标位置的完整路径，包括：
- 每个中间变量的名称
- 每次传递/赋值的位置（文件:行号）
- 每次传递的方式（方法调用、参数传递、属性访问等）

### 4. 处理多个来源

如果数据有多个可能来源（如条件分支），分别追踪每个来源：

```java
// 示例：多来源情况
String value;
if (condition) {
    value = source1.getValue();  // 来源1
} else {
    value = source2.getValue();  // 来源2
}
```

需要说明：
- 来源1的路径和条件
- 来源2的路径和条件

### 5. 跨文件追踪

当数据流跨越多个文件时：

```bash
# 搜索方法定义
grep -rn "methodName(" src/

# 读取方法所在文件
# (使用 Read 工具)
```

记录跨文件的传递链条。

## 输出格式

使用 **data-flow-tracing** Skill 的标准输出格式：

```markdown
## 数据来源追踪结果

### 目标数据：[变量名/位置]

**原始来源**：
- [来源类型]：[具体描述]
- 位置：[文件名:行号]
- 说明：[如何获取的详细说明]

**传递路径**：
1. [步骤1] - [文件名:行号]
   - 说明：[这一步做了什么]
2. [步骤2] - [文件名:行号]
   - 说明：[这一步做了什么]
3. ...

**完整链路图**：
```
[原始来源] → [中间变量1] → [中间变量2] → ... → [目标变量]
```

**附加信息**（如适用）：
- 多来源情况：[说明不同条件下的不同来源]
- 不确定因素：[需要进一步确认的点]
- 相关方法：[涉及的关键方法列表]
```

## 示例

### 示例 1：简单追踪

**用户输入**：`/trace-data-source userName`

**输出**：
```markdown
## 数据来源追踪结果

### 目标数据：userName

**原始来源**：
- 来源类型：方法参数
- 位置：UserController.java:23
- 说明：从 HTTP 请求参数 `UserRequest.getName()` 获取

**传递路径**：
1. HTTP 请求解析 → `UserRequest` 对象 - UserController.java:20
2. 调用 `request.getName()` → `userName` 变量 - UserController.java:23
3. 传递给 `userService.processUser(userName)` - UserController.java:24

**完整链路图**：
```
HTTP Request Body → UserRequest.name → userName → userService
```
```

### 示例 2：复杂追踪

**用户输入**：`/trace-data-source finalPrice`

**输出**：
```markdown
## 数据来源追踪结果

### 目标数据：finalPrice

**原始来源**：
- 来源1：`product.getPrice()` - 从数据库查询的产品价格
  - 位置：OrderService.java:45
- 来源2：`user.getDiscountRate()` - 从用户对象获取的折扣率
  - 位置：OrderService.java:46

**传递路径**：
1. 数据库查询产品 → `Product` 对象 - ProductRepository.java:30
2. 提取价格 → `originalPrice = product.getPrice()` - OrderService.java:45
3. 获取折扣率 → `discountRate = user.getDiscountRate()` - OrderService.java:46
4. 计算折扣 → `discount = originalPrice.multiply(discountRate)` - OrderService.java:47
5. 计算最终价格 → `finalPrice = originalPrice.subtract(discount)` - OrderService.java:48

**完整链路图**：
```
product (DB) → getPrice() → originalPrice ──┐
                                             ├→ multiply → subtract → finalPrice
user → getDiscountRate() → discountRate ────┘
```

**附加信息**：
- `originalPrice` 单位为元（BigDecimal）
- `discountRate` 为小数形式（如 0.1 表示 10% 折扣）
- 计算过程保留两位小数
```

## 注意事项

1. **仅追踪数据来源**：不评价代码质量，不提供优化建议
2. **准确定位代码**：始终包含文件名和行号
3. **完整追踪链路**：从原始来源到目标位置，不遗漏中间步骤
4. **说明不确定性**：如果无法完全确定来源，明确指出需要进一步调查的点
5. **避免过度追踪**：追踪到明确的原始来源即可（如数据库、配置、参数等），无需追踪到框架底层

## 工具使用优先级

1. **Read** - 读取具体文件内容
2. **Grep** - 搜索变量名、方法调用
3. **Glob** - 查找相关文件模式
4. **Bash (git)** - 查看历史修改（必要时）

**避免**：广泛扫描整个项目，优先分析用户关注的具体代码区域。
