---
name: data-flow-tracing
description: 当用户询问"数据从哪来"、"变量如何计算"、"追踪数据流"、"这个值是怎么得到的"、"数据如何转换"等与数据来源、计算、流动相关的问题时，使用此技能进行数据流分析
---

# 数据流追踪分析方法论

本技能专注于分析代码中的数据流动：数据的来源、计算过程、转换路径和最终用途。

## 分析目标

专注于回答以下问题：
- 数据从哪里来？（来源）
- 数据如何被计算？（转换）
- 数据流向哪里？（用途）
- 数据经过了哪些中间状态？（路径）

**重要**：仅分析数据流动，不评估代码质量、安全性或性能。

## 数据来源识别

### 常见数据来源类型

1. **方法参数**
   - 直接传入的参数
   - 参数对象的属性（如 `request.getUserId()`）
   - 嵌套对象的深层属性（如 `contract.getPromiseInfo().getStatus()`）

2. **方法调用返回值**
   - 其他服务方法的返回（如 `userService.getUser(id)`）
   - 工具类方法（如 `StringUtils.trim(name)`）
   - 构造器创建（如 `new ArrayList<>()`）

3. **数据库查询**
   - DAO/Repository 方法
   - MyBatis Mapper 调用
   - JPA 查询

4. **外部 API**
   - HTTP 请求返回
   - RPC 调用结果
   - 第三方服务响应

5. **配置和常量**
   - 配置文件读取
   - 静态常量
   - 环境变量

6. **本地计算**
   - 字面量（`"value"`, `100`, `true`）
   - 表达式计算（`a + b`, `x * 2`）
   - 条件分支赋值

### 来源追踪示例

```java
// 示例代码
String userName = userRequest.getUserName();
String processedName = nameProcessor.process(userName);
userRepository.save(processedName);
```

**数据流分析**：
- `userName` 来源：方法参数 `userRequest` 的 `getUserName()` 方法返回值
- `processedName` 来源：`nameProcessor.process()` 方法对 `userName` 的转换结果
- 最终用途：通过 `userRepository.save()` 保存到数据库

## 数据计算和转换分析

### 转换类型

1. **类型转换**
   ```java
   String idStr = request.getParameter("id");
   Long id = Long.parseLong(idStr);  // String → Long
   ```

2. **映射转换**
   ```java
   List<User> users = userService.getUsers();
   List<String> names = users.stream()
       .map(User::getName)  // User → String
       .collect(Collectors.toList());
   ```

3. **过滤筛选**
   ```java
   List<Order> orders = getAllOrders();
   List<Order> activeOrders = orders.stream()
       .filter(o -> o.getStatus() == Status.ACTIVE)  // 筛选条件
       .collect(Collectors.toList());
   ```

4. **聚合计算**
   ```java
   List<Integer> prices = getPrices();
   Integer total = prices.stream()
       .reduce(0, Integer::sum);  // 累加求和
   ```

5. **组合构造**
   ```java
   String firstName = user.getFirstName();
   String lastName = user.getLastName();
   String fullName = firstName + " " + lastName;  // 字符串拼接
   ```

6. **条件分支**
   ```java
   Integer discount;
   if (user.isVip()) {
       discount = 20;  // VIP 折扣
   } else {
       discount = 10;  // 普通折扣
   }
   ```

### 计算链分析

追踪多步转换的完整链条：

```java
// 示例：价格计算链
BigDecimal originalPrice = product.getPrice();           // 来源：产品对象
BigDecimal discountRate = user.getDiscountRate();        // 来源：用户对象
BigDecimal discountAmount = originalPrice.multiply(discountRate);  // 计算1：折扣金额
BigDecimal finalPrice = originalPrice.subtract(discountAmount);    // 计算2：最终价格
```

**数据流描述**：
1. `originalPrice` ← `product.getPrice()` (产品原价)
2. `discountRate` ← `user.getDiscountRate()` (用户折扣率)
3. `discountAmount` ← `originalPrice × discountRate` (计算折扣金额)
4. `finalPrice` ← `originalPrice - discountAmount` (计算最终价格)

## 数据流路径追踪

### 跨方法追踪

```java
public void processOrder(OrderRequest request) {
    Order order = buildOrder(request);  // 步骤1：构建订单
    validate(order);                     // 步骤2：验证
    save(order);                         // 步骤3：保存
}

private Order buildOrder(OrderRequest request) {
    Order order = new Order();
    order.setUserId(request.getUserId());        // 数据传递
    order.setAmount(calculateAmount(request));   // 数据计算
    return order;
}

private BigDecimal calculateAmount(OrderRequest request) {
    return request.getPrice().multiply(request.getQuantity());
}
```

**完整数据流**：
- `request.getUserId()` → `order.setUserId()` → 保存到数据库
- `request.getPrice()` × `request.getQuantity()` → `calculateAmount()` 返回 → `order.setAmount()` → 保存到数据库

### 跨类追踪

```java
// Controller
public void handleRequest(UserRequest request) {
    Long userId = request.getUserId();
    userService.updateUser(userId);  // 传递给 Service
}

// Service
public void updateUser(Long userId) {
    User user = userRepository.findById(userId);  // 用于查询
    // ...
}
```

**数据流路径**：
`UserRequest.getUserId()` → Controller 方法参数 → Service 方法参数 → Repository 查询条件

## 分析输出格式

### 标准输出结构

```markdown
## 数据流分析结果

### 变量: [变量名]

**来源**：
- [描述数据的原始来源]
- 文件：[文件名:行号]

**计算过程**：
1. [步骤1描述] - [文件名:行号]
2. [步骤2描述] - [文件名:行号]
3. ...

**最终用途**：
- [数据如何被使用]
- 文件：[文件名:行号]

**完整路径**：
[来源] → [转换1] → [转换2] → ... → [用途]
```

### 示例输出

```markdown
## 数据流分析结果

### 变量: finalAmount

**来源**：
- 方法参数 `contractReq` 的 `getPromiseInfo().getAmount()` 返回值
- 文件：ContractService.java:45

**计算过程**：
1. 获取原始金额：`promiseAmount = contractReq.getPromiseInfo().getAmount()` - ContractService.java:45
2. 应用折扣率：`discountedAmount = promiseAmount.multiply(DISCOUNT_RATE)` - ContractService.java:47
3. 添加手续费：`finalAmount = discountedAmount.add(FEE)` - ContractService.java:48

**最终用途**：
- 设置到合同对象：`contract.setFinalAmount(finalAmount)`
- 文件：ContractService.java:50

**完整路径**：
contractReq → getPromiseInfo() → getAmount() → multiply(DISCOUNT_RATE) → add(FEE) → contract.setFinalAmount()
```

## 分析技巧

### 1. 使用 Grep 定位变量定义和使用

```bash
# 查找变量定义
grep -n "variableName =" file.java

# 查找变量使用
grep -n "variableName" file.java
```

### 2. 追踪方法调用链

从目标变量开始，逆向追踪每个赋值操作的右侧表达式，直到找到原始数据源。

### 3. 识别关键转换点

重点关注：
- 类型转换操作
- Stream API 的 map/filter/reduce
- 算术运算
- 字符串操作
- 对象构造

### 4. 处理复杂数据流

对于复杂的数据流（多个来源、多次转换），建议：
1. 先识别所有原始来源
2. 列出所有中间变量
3. 绘制数据流图
4. 逐步描述每个转换

### 5. 跨文件追踪

当数据流跨越多个文件时：
1. 使用 Grep 查找方法调用
2. 读取相关文件了解方法实现
3. 记录每个文件的数据转换
4. 汇总完整路径

## 常见场景

### 场景1：追踪 null 值来源

用户问："为什么这个变量是 null？"

**分析步骤**：
1. 定位变量赋值点
2. 追踪赋值来源（方法返回、属性访问等）
3. 检查来源方法的返回条件
4. 识别可能返回 null 的分支

### 场景2：理解复杂计算

用户问："这个金额是怎么算出来的？"

**分析步骤**：
1. 找到最终变量的赋值
2. 展开计算表达式
3. 追踪每个参与计算的变量来源
4. 列出完整计算公式

### 场景3：定位数据修改

用户问："这个字段在哪里被改了？"

**分析步骤**：
1. Grep 查找所有赋值操作
2. 分析每个赋值的条件和时机
3. 追踪修改的触发路径
4. 说明修改的原因和影响

## 注意事项

### 仅关注数据流

- ✅ 描述数据从哪来、怎么算、到哪去
- ❌ 不评价代码好坏
- ❌ 不提供重构建议
- ❌ 不分析性能问题
- ❌ 不检查安全漏洞

### 保持客观描述

- 使用事实性语言："变量 X 来自方法 Y 的返回值"
- 避免主观评价："这个实现很糟糕"
- 专注于 what/how，而非 should/could

### 准确定位代码位置

始终提供文件名和行号，方便用户验证：
- `ContractService.java:45`
- `src/main/java/com/example/UserController.java:123`

### 处理不确定性

如果无法确定数据来源，明确说明：
- "此变量可能来自以下几个地方：..."
- "需要查看 X 方法的实现才能确定"
- "数据流在此处分叉，取决于条件 Y"

## 工具使用建议

- **Read**：读取相关源文件
- **Grep**：搜索变量名、方法调用
- **Glob**：查找相关文件（如 *Service.java, *Repository.java）
- **Bash (git)**：查看历史修改（如 `git log -p -- file.java`）

优先使用 Read 和 Grep，避免广泛扫描整个项目。

---

**使用此技能时，始终记住：我们是数据侦探，追踪数据的足迹，不是代码审查员。**
