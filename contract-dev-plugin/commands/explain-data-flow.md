---
description: 解释一段代码中的完整数据流动，包括数据的来源、转换、计算和最终用途。使用 data-flow-tracing Skill。
argument-hint: "[文件名、方法名或留空分析当前修改]"
allowed-tools: Read, Grep, Glob, Bash(git diff:*), Bash(git show:*)
---

## 任务目标

全面分析一段代码中的数据流动，回答"这段代码中数据是如何流动的？"

## 输入信息

### 用户指定的分析范围

- **如果用户提供了文件名**：分析该文件中的数据流
  - 示例：`/explain-data-flow OrderService.java`
  - 示例：`/explain-data-flow src/main/java/com/example/ContractService.java`

- **如果用户提供了方法名**：分析该方法的数据流
  - 示例：`/explain-data-flow processOrder`
  - 示例：`/explain-data-flow ContractService.createContract`

- **如果用户提供了代码片段**：分析该片段的数据流
  - 示例：用户选中一段代码后运行命令

- **如果用户未提供明确范围**：分析当前修改的代码的数据流
  - 获取 git diff
  - 分析修改涉及的数据流动

### 当前代码上下文

- 当前分支：!`git branch --show-current`
- 当前修改：!`git diff HEAD`（如果分析修改）
- 工作目录：!`pwd`

## 执行步骤

### 1. 确定分析范围

根据用户输入，确定要分析的代码范围：

```bash
# 如果是文件名，读取整个文件
# (使用 Read 工具)

# 如果是方法名，搜索方法定义
grep -rn "methodName(" src/

# 如果是当前修改，获取 diff
git diff HEAD
```

### 2. 识别所有数据实体

在代码范围内，识别所有重要的数据实体：

- **变量**：局部变量、成员变量
- **参数**：方法参数、构造器参数
- **返回值**：方法返回值
- **对象属性**：通过 getter/setter 访问的属性
- **集合元素**：List、Map、Set 中的元素
- **数据库实体**：从数据库读取或写入的数据
- **DTO/VO**：数据传输对象

按照重要性排序，重点关注：
1. 方法主要处理的数据（如订单、用户、合同等）
2. 计算结果和中间变量
3. 传递给其他方法的数据
4. 返回给调用方的数据

### 3. 追踪每个数据实体的流动

对于每个重要数据实体，追踪其完整生命周期：

#### A. 数据来源

数据从哪里来？
- 方法参数
- 数据库查询
- 其他方法返回
- 配置读取
- 计算生成
- 常量/字面量

#### B. 数据转换

数据经历了哪些转换？
- 类型转换（String → Integer）
- 对象映射（Entity → DTO）
- 集合转换（List → Map）
- 计算操作（加减乘除）
- 格式化（日期、金额格式化）
- 过滤筛选（Stream filter）

#### C. 数据用途

数据最终去向？
- 作为返回值返回
- 传递给其他方法
- 保存到数据库
- 写入文件/缓存
- 发送到外部 API
- 仅作为中间变量

### 4. 绘制数据流图

将数据流动可视化为流程图或路径图：

**简单流图**（单路径）：
```
来源 → 转换1 → 转换2 → 用途
```

**复杂流图**（多路径）：
```
来源A ──┐
        ├→ 合并 → 转换 → 用途1
来源B ──┘           └→ 用途2
```

**分支流图**（条件分支）：
```
       ┌→ 分支A → 用途A
来源 ──┤
       └→ 分支B → 用途B
```

### 5. 识别数据依赖关系

说明数据之间的依赖关系：

- **数据X 依赖于 数据Y**：X 的计算需要 Y
- **数据X 影响 数据Y**：X 的值决定 Y 的计算
- **数据X 和 Y 独立**：两者无直接关系

### 6. 分析关键数据节点

识别数据流中的关键节点：

- **数据汇聚点**：多个数据源汇聚到一个变量
- **数据分发点**：一个数据被多处使用
- **数据转换点**：数据类型或结构发生重大变化
- **数据验证点**：数据被检查或验证
- **数据持久化点**：数据被保存到存储

### 7. 按时间顺序整理流程

将数据流动按代码执行顺序整理：

1. 第一步：获取/初始化数据
2. 第二步：验证或处理数据
3. 第三步：转换或计算数据
4. 第四步：使用或保存数据
5. ...

## 输出格式

```markdown
## 数据流分析结果

### 分析范围
- 文件：[文件名]
- 方法：[方法名]（如适用）
- 行号范围：[起始行-结束行]

### 数据实体清单

| 变量名 | 类型 | 来源 | 用途 |
|--------|------|------|------|
| data1  | String | 方法参数 | 保存到数据库 |
| data2  | BigDecimal | 计算得出 | 返回给调用方 |
| ...    | ...  | ...  | ...  |

### 完整数据流图

```
[流程图或路径图]
```

### 详细流程说明

#### 步骤 1：[步骤标题]
- **代码位置**：[文件名:行号]
- **操作**：[具体操作描述]
- **涉及数据**：
  - 输入：`data1`, `data2`
  - 输出：`result`
- **说明**：[这一步的目的和作用]

#### 步骤 2：[步骤标题]
- **代码位置**：[文件名:行号]
- **操作**：[具体操作描述]
- **涉及数据**：
  - 输入：`result`
  - 输出：`finalData`
- **说明**：[这一步的目的和作用]

...

### 关键数据节点

1. **[节点名称]** - [文件名:行号]
   - 类型：[汇聚点/分发点/转换点/验证点/持久化点]
   - 说明：[为什么这是关键节点]
   - 涉及数据：[相关数据列表]

2. ...

### 数据依赖关系

- `finalPrice` 依赖于 `originalPrice` 和 `discount`
- `userInfo` 影响 `orderInfo` 的创建
- `productList` 独立于 `userList`
- ...

### 总结

[一段简短的总结，描述整体数据流的主要特点和关键路径]
```

## 示例

### 示例：分析订单处理方法

**用户输入**：`/explain-data-flow processOrder`

**输出**：
```markdown
## 数据流分析结果

### 分析范围
- 文件：OrderService.java
- 方法：processOrder(OrderRequest request)
- 行号范围：45-80

### 数据实体清单

| 变量名 | 类型 | 来源 | 用途 |
|--------|------|------|------|
| request | OrderRequest | 方法参数 | 提取订单信息 |
| userId | Long | request.getUserId() | 查询用户信息 |
| user | User | 数据库查询 | 获取用户折扣率 |
| productIds | List<Long> | request.getProductIds() | 查询商品信息 |
| products | List<Product> | 数据库查询 | 计算订单金额 |
| totalAmount | BigDecimal | 计算得出 | 设置订单金额 |
| order | Order | 构造创建 | 保存到数据库 |

### 完整数据流图

```
request (参数) ──┬→ getUserId() → userId → 查询 user
                 │                           ↓
                 │                     getDiscountRate()
                 │                           ↓
                 └→ getProductIds() → productIds → 查询 products
                                                     ↓
                                                getPrice()
                                                     ↓
                                            计算 → totalAmount
                                                     ↓
                                            构造 → order → 保存到DB
```

### 详细流程说明

#### 步骤 1：提取用户ID
- **代码位置**：OrderService.java:48
- **操作**：从请求对象中提取用户ID
- **涉及数据**：
  - 输入：`request`
  - 输出：`userId`
- **代码**：`Long userId = request.getUserId()`
- **说明**：获取下单用户的ID，用于后续查询用户信息

#### 步骤 2：查询用户信息
- **代码位置**：OrderService.java:49
- **操作**：根据用户ID从数据库查询用户详情
- **涉及数据**：
  - 输入：`userId`
  - 输出：`user`
- **代码**：`User user = userRepository.findById(userId).orElseThrow()`
- **说明**：获取用户对象，后续需要使用用户的折扣率信息

#### 步骤 3：提取商品ID列表
- **代码位置**：OrderService.java:52
- **操作**：从请求对象中提取商品ID列表
- **涉及数据**：
  - 输入：`request`
  - 输出：`productIds`
- **代码**：`List<Long> productIds = request.getProductIds()`
- **说明**：获取订单包含的所有商品ID

#### 步骤 4：批量查询商品信息
- **代码位置**：OrderService.java:53
- **操作**：根据商品ID列表批量查询商品详情
- **涉及数据**：
  - 输入：`productIds`
  - 输出：`products`
- **代码**：`List<Product> products = productRepository.findAllById(productIds)`
- **说明**：获取商品对象列表，包含商品价格等信息

#### 步骤 5：计算订单总金额
- **代码位置**：OrderService.java:56-60
- **操作**：计算所有商品的总价，并应用用户折扣
- **涉及数据**：
  - 输入：`products`, `user`
  - 输出：`totalAmount`
- **代码**：
  ```java
  BigDecimal subtotal = products.stream()
      .map(Product::getPrice)
      .reduce(BigDecimal.ZERO, BigDecimal::add);
  BigDecimal discountRate = user.getDiscountRate();
  BigDecimal totalAmount = subtotal.multiply(BigDecimal.ONE.subtract(discountRate));
  ```
- **说明**：
  1. 累加所有商品价格得到小计
  2. 获取用户折扣率
  3. 应用折扣计算最终金额

#### 步骤 6：构造订单对象
- **代码位置**：OrderService.java:63-68
- **操作**：创建订单对象并设置各个字段
- **涉及数据**：
  - 输入：`userId`, `totalAmount`, `products`
  - 输出：`order`
- **代码**：
  ```java
  Order order = new Order();
  order.setUserId(userId);
  order.setTotalAmount(totalAmount);
  order.setProducts(products);
  order.setStatus(OrderStatus.PENDING);
  ```
- **说明**：组装订单对象，准备持久化

#### 步骤 7：保存订单
- **代码位置**：OrderService.java:71
- **操作**：将订单对象保存到数据库
- **涉及数据**：
  - 输入：`order`
  - 输出：持久化的 `order`（带ID）
- **代码**：`Order savedOrder = orderRepository.save(order)`
- **说明**：持久化订单数据，数据库分配订单ID

#### 步骤 8：返回订单
- **代码位置**：OrderService.java:73
- **操作**：返回已保存的订单对象
- **涉及数据**：
  - 输入：`savedOrder`
  - 输出：返回值
- **代码**：`return savedOrder`
- **说明**：将订单返回给调用方（通常是 Controller）

### 关键数据节点

1. **数据汇聚点：totalAmount 计算** - OrderService.java:56-60
   - 类型：汇聚点 + 转换点
   - 说明：多个商品价格汇聚，经过累加和折扣计算，得出最终金额
   - 涉及数据：`products` (List)、`user.discountRate`、`totalAmount`

2. **数据分发点：request 参数** - OrderService.java:45
   - 类型：分发点
   - 说明：请求对象包含多个字段，分别被提取用于不同用途
   - 涉及数据：`userId`、`productIds`、其他请求字段

3. **数据持久化点：订单保存** - OrderService.java:71
   - 类型：持久化点
   - 说明：订单数据从内存对象转为数据库记录
   - 涉及数据：`order` → 数据库 `t_order` 表

### 数据依赖关系

- `totalAmount` 依赖于 `products` 和 `user.discountRate`
- `order` 依赖于 `userId`、`totalAmount`、`products`
- `savedOrder` 依赖于 `order`（需要先构造才能保存）
- `userId` 和 `productIds` 相互独立（来自不同字段）

### 总结

该方法的数据流主要分为三个阶段：
1. **数据获取阶段**：从请求参数提取信息，查询用户和商品数据
2. **数据计算阶段**：根据商品价格和用户折扣计算订单总金额
3. **数据持久化阶段**：构造订单对象并保存到数据库

核心数据流是：`request` → 提取字段 → 查询关联数据 → 计算金额 → 构造订单 → 保存订单 → 返回结果。关键计算节点是 `totalAmount` 的计算，它汇聚了商品价格和用户折扣信息。
```

## 注意事项

1. **全局视角**：不仅关注单个变量，要理解整段代码的数据流动全貌
2. **结构化展示**：使用表格、流程图、分步说明等多种形式清晰展示
3. **突出重点**：识别并强调关键数据节点和主要数据流路径
4. **完整追踪**：从数据来源追踪到最终用途，不遗漏中间步骤
5. **代码定位**：每个步骤都标注准确的代码位置
6. **适度详细**：根据代码复杂度调整详细程度，避免过于冗长或过于简略
7. **仅描述数据流**：不评价代码质量，不提供优化建议

## 工具使用

- **Read**：读取源文件
- **Grep**：搜索方法、变量
- **Glob**：查找相关文件
- **Bash (git)**：获取代码修改（如需要）

优先分析用户关注的代码区域，避免无关代码的干扰。
