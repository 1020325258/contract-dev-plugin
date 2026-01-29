---
description: 分析数据的计算和转换过程，解释计算逻辑、公式、中间步骤。使用 data-flow-tracing Skill。
argument-hint: "[变量名或计算表达式]"
allowed-tools: Read, Grep, Glob
---

## 任务目标

分析数据的计算和转换过程，回答"这个值是怎么算出来的？"

## 输入信息

### 用户指定的目标

- **如果用户提供了变量名**：分析该变量的计算过程
  - 示例：`/analyze-calculation finalAmount`
  - 示例：`/analyze-calculation totalPrice`

- **如果用户提供了表达式或代码片段**：分析该表达式的计算逻辑
  - 示例：`/analyze-calculation price * quantity - discount`
  - 示例：`/analyze-calculation users.stream().map(...).collect(...)`

- **如果用户提供了方法名**：分析该方法的计算逻辑
  - 示例：`/analyze-calculation calculateDiscount`
  - 示例：`/analyze-calculation computeFinalPrice`

- **如果用户未提供明确目标**：分析当前修改代码中的主要计算逻辑
  - 获取 git diff 查看修改
  - 识别计算相关的代码
  - 分析计算过程

### 当前代码上下文

- 当前分支：!`git branch --show-current`
- 当前修改：!`git diff HEAD`（如果需要）

## 执行步骤

### 1. 定位计算代码

根据用户输入，找到相关的计算代码：

```bash
# 搜索变量赋值和计算
grep -rn "variableName.*=" src/

# 搜索方法定义
grep -rn "methodName(" src/
```

使用 **Read** 工具读取相关文件。

### 2. 识别计算类型

判断计算属于哪种类型，采用对应的分析方法：

#### 类型 1：算术运算

```java
BigDecimal finalPrice = originalPrice.multiply(quantity).subtract(discount);
```

**分析要点**：
- 每个操作符的含义（加、减、乘、除）
- 操作数的来源
- 运算顺序和优先级
- 中间结果

#### 类型 2：Stream 转换

```java
List<String> names = users.stream()
    .filter(u -> u.isActive())
    .map(User::getName)
    .collect(Collectors.toList());
```

**分析要点**：
- 输入数据（原始集合）
- 每个 Stream 操作的作用（filter、map、reduce 等）
- 转换逻辑（lambda 表达式）
- 输出结果

#### 类型 3：条件计算

```java
Integer discount = user.isVip()
    ? calculateVipDiscount(order)
    : calculateNormalDiscount(order);
```

**分析要点**：
- 分支条件
- 每个分支的计算逻辑
- 不同情况下的结果

#### 类型 4：循环累积

```java
BigDecimal total = BigDecimal.ZERO;
for (OrderItem item : items) {
    total = total.add(item.getPrice());
}
```

**分析要点**：
- 初始值
- 迭代逻辑
- 累积操作
- 终止条件

#### 类型 5：类型转换

```java
String amountStr = "100.50";
BigDecimal amount = new BigDecimal(amountStr);
Integer cents = amount.multiply(new BigDecimal(100)).intValue();
```

**分析要点**：
- 原始类型
- 目标类型
- 转换方法
- 精度和舍入规则

#### 类型 6：对象构造和映射

```java
UserDTO dto = UserDTO.builder()
    .id(user.getId())
    .name(user.getName())
    .age(calculateAge(user.getBirthDate()))
    .build();
```

**分析要点**：
- 源对象
- 目标对象
- 字段映射关系
- 计算转换的字段

### 3. 追踪计算输入

对于计算中使用的每个变量，说明其来源：

- 如果是常量：说明常量的值和含义
- 如果是变量：简要说明变量来源（详细来源可用 `/trace-data-source`）
- 如果是方法调用：说明方法的作用和返回值

### 4. 展开计算步骤

将复杂计算展开为多个步骤，每步说明：

- **步骤编号**
- **操作内容**：做了什么计算/转换
- **输入**：使用了哪些数据
- **输出**：产生了什么结果
- **代码位置**：文件名:行号

### 5. 生成计算公式

如果是数学计算，用公式表示：

```
finalPrice = (originalPrice × quantity) - discount
           = (100 × 3) - 50
           = 300 - 50
           = 250
```

如果是复杂转换，用流程表示：

```
输入：List<User>
  ↓ filter(u -> u.isActive())
中间：List<User> (仅活跃用户)
  ↓ map(User::getName)
中间：Stream<String>
  ↓ collect(Collectors.toList())
输出：List<String>
```

### 6. 处理嵌套计算

对于多层嵌套的计算，采用自顶向下或自底向上的方式展开：

**自顶向下**（从结果到输入）：
```
finalAmount
  └─ calculateTotal(items)
       ├─ items.stream().map(Item::getPrice)
       └─ .reduce(BigDecimal.ZERO, BigDecimal::add)
```

**自底向上**（从输入到结果）：
```
items → getPrice() → Stream<BigDecimal> → reduce(sum) → total
```

## 输出格式

使用清晰的结构化格式：

```markdown
## 计算过程分析结果

### 目标计算：[变量名/表达式]

**计算类型**：[算术运算/Stream转换/条件计算/循环累积/类型转换/对象映射]

**代码位置**：[文件名:行号]

**输入数据**：
- `input1`：[来源和含义] - [值/类型]
- `input2`：[来源和含义] - [值/类型]
- ...

**计算步骤**：
1. [步骤描述]
   - 操作：[具体操作]
   - 输入：[使用的数据]
   - 输出：[产生的结果]
   - 位置：[文件名:行号]

2. [步骤描述]
   - 操作：[具体操作]
   - 输入：[使用的数据]
   - 输出：[产生的结果]
   - 位置：[文件名:行号]

3. ...

**计算公式**（如适用）：
```
[数学公式或伪代码]
```

**示例计算**（如适用）：
```
假设输入：input1 = X, input2 = Y
步骤1：X ○ Y = Z
步骤2：Z ○ W = Result
```

**最终结果**：
- 类型：[结果的数据类型]
- 含义：[结果代表什么]
- 用途：[结果如何被使用]
```

## 示例

### 示例 1：算术运算

**用户输入**：`/analyze-calculation finalPrice`

**输出**：
```markdown
## 计算过程分析结果

### 目标计算：finalPrice

**计算类型**：算术运算

**代码位置**：OrderService.java:48-50

**输入数据**：
- `originalPrice`：产品原价 - BigDecimal (来自 product.getPrice())
- `quantity`：购买数量 - Integer (来自 orderRequest.getQuantity())
- `discount`：折扣金额 - BigDecimal (来自 calculateDiscount())

**计算步骤**：
1. 计算小计
   - 操作：原价 × 数量
   - 输入：originalPrice, quantity
   - 输出：subtotal
   - 位置：OrderService.java:48
   - 代码：`BigDecimal subtotal = originalPrice.multiply(new BigDecimal(quantity))`

2. 应用折扣
   - 操作：小计 - 折扣
   - 输入：subtotal, discount
   - 输出：finalPrice
   - 位置：OrderService.java:50
   - 代码：`BigDecimal finalPrice = subtotal.subtract(discount)`

**计算公式**：
```
finalPrice = (originalPrice × quantity) - discount
```

**示例计算**：
```
假设输入：
- originalPrice = 100.00
- quantity = 3
- discount = 50.00

计算：
步骤1：100.00 × 3 = 300.00
步骤2：300.00 - 50.00 = 250.00
```

**最终结果**：
- 类型：BigDecimal
- 含义：订单最终应付金额（元）
- 用途：保存到订单对象 order.setFinalPrice(finalPrice)
```

### 示例 2：Stream 转换

**用户输入**：`/analyze-calculation activeUserNames`

**输出**：
```markdown
## 计算过程分析结果

### 目标计算：activeUserNames

**计算类型**：Stream 转换（过滤 + 映射）

**代码位置**：UserService.java:65-68

**输入数据**：
- `users`：所有用户列表 - List<User> (来自 userRepository.findAll())

**计算步骤**：
1. 创建 Stream
   - 操作：将 List 转为 Stream
   - 输入：users (List<User>)
   - 输出：Stream<User>
   - 位置：UserService.java:65

2. 过滤活跃用户
   - 操作：filter(u -> u.getStatus() == UserStatus.ACTIVE)
   - 输入：Stream<User> (所有用户)
   - 输出：Stream<User> (仅活跃用户)
   - 位置：UserService.java:66
   - 说明：保留 status 为 ACTIVE 的用户

3. 提取用户名
   - 操作：map(User::getName)
   - 输入：Stream<User> (活跃用户)
   - 输出：Stream<String> (用户名)
   - 位置：UserService.java:67
   - 说明：从每个 User 对象提取 name 字段

4. 收集结果
   - 操作：collect(Collectors.toList())
   - 输入：Stream<String>
   - 输出：List<String>
   - 位置：UserService.java:68
   - 说明：将 Stream 转换回 List

**转换流程图**：
```
List<User> (所有用户，100个)
  ↓ stream()
Stream<User>
  ↓ filter(status == ACTIVE)
Stream<User> (活跃用户，60个)
  ↓ map(User::getName)
Stream<String>
  ↓ collect(toList)
List<String> (活跃用户名列表，60个)
```

**最终结果**：
- 类型：List<String>
- 含义：所有活跃用户的姓名列表
- 用途：用于生成活跃用户报表
```

## 注意事项

1. **仅分析计算逻辑**：说明计算如何进行，不评价计算是否正确或高效
2. **展开复杂表达式**：将复杂的链式调用或嵌套计算拆分为清晰的步骤
3. **说明中间状态**：对于多步计算，说明每步的中间结果
4. **使用具体示例**：如果可能，用具体数值演示计算过程
5. **标注代码位置**：每个步骤都标注对应的代码位置（文件:行号）
6. **处理分支逻辑**：如果计算有多个分支，分别说明每个分支的计算逻辑
7. **避免过度展开**：对于简单的 getter 调用或基本运算，无需过度详细

## 工具使用

- **Read**：读取包含计算代码的文件
- **Grep**：搜索变量、方法、表达式
- **Glob**：查找相关文件（如 *Service.java, *Calculator.java）

优先阅读用户关注的代码区域，避免无关文件的读取。
