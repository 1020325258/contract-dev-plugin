---
description: 快速分析当前修改代码中的数据流动，自动识别重要数据并追踪其来源、计算和用途。使用 data-flow-tracing Skill。
allowed-tools: Bash(git status:*), Bash(git diff:*), Bash(git branch:*), Read, Grep, Glob
---

## 任务目标

快速分析当前 git 修改中的数据流动，自动识别新增或修改的数据，追踪其来源、计算过程和用途。

## 当前分支信息

- 当前分支：!`git branch --show-current`
- 状态：!`git status --porcelain`
- diff（当前修改和 HEAD 的差异）：!`git diff HEAD`

## 执行步骤

### 1. 分析 Git Diff

从 git diff 输出中识别：
- 新增的变量赋值（`+` 开头的行中的 `= ` 语句）
- 修改的计算逻辑
- 新增的方法调用
- 修改的数据传递

### 2. 识别关键数据实体

从 diff 中提取重要的数据实体，优先级：
1. 新增的变量（特别是方法返回值、计算结果）
2. 修改的变量赋值
3. 新增的方法参数
4. 修改的对象属性访问

忽略：
- 日志语句中的字符串
- 注释
- 格式化调整
- import 语句

### 3. 对每个关键数据实体进行分析

使用 **data-flow-tracing** Skill 的方法，对每个实体分析：
- **来源**：数据从哪里来？
- **计算**：数据如何被转换或计算？（如果有）
- **用途**：数据最终去哪里？

### 4. 识别数据流变化

对比修改前后的数据流：
- 新增了哪些数据流路径？
- 修改了哪些数据来源？
- 改变了哪些计算逻辑？

### 5. 读取相关文件

当需要完整上下文时，读取修改涉及的文件：

```bash
# 获取修改的文件列表
git diff HEAD --name-only
```

使用 **Read** 工具读取这些文件，了解：
- 方法的完整实现
- 变量的所有使用位置
- 相关方法的定义

### 6. 处理跨文件数据流

如果数据流跨越文件边界：
- 使用 **Grep** 搜索方法调用
- 读取相关文件了解数据传递
- 追踪跨文件的完整路径

## 输出格式

```markdown
## 当前修改的数据流分析

### 修改概览
- 分支：[分支名]
- 修改文件：[文件列表]
- 新增/修改的关键数据：[数量]

### 关键数据分析

#### 1. 数据：[变量名]
**位置**：[文件名:行号]（新增/修改）

**来源**：
- [数据来源描述]

**计算**（如适用）：
- [计算过程描述]

**用途**：
- [数据如何被使用]

**数据流路径**：
```
[来源] → [转换] → [用途]
```

#### 2. 数据：[另一个变量]
[同样的结构...]

### 数据流变化摘要

**新增数据流**：
- [新增的数据流路径1]
- [新增的数据流路径2]

**修改数据流**：
- [修改前] → [修改后]

**影响范围**：
- [这些修改影响了哪些数据/方法/功能]

### 建议关注点

如果发现需要特别关注的数据流问题（非代码质量评价），提示：
- 多来源数据：[某数据有多个可能来源，需明确条件]
- 复杂计算：[某计算较复杂，建议用 /analyze-calculation 详细分析]
- 跨文件流动：[某数据流跨多个文件，可用 /trace-data-source 完整追踪]
```

## 示例输出

```markdown
## 当前修改的数据流分析

### 修改概览
- 分支：feature/add-discount
- 修改文件：OrderService.java, OrderController.java
- 新增/修改的关键数据：3个

### 关键数据分析

#### 1. 数据：discountAmount (新增)
**位置**：OrderService.java:47

**来源**：
- 计算得出，依赖于 `originalPrice` (来自 product.getPrice()) 和 `discountRate` (来自 user.getDiscountRate())

**计算**：
- `discountAmount = originalPrice.multiply(discountRate)`
- 原价乘以折扣率得出折扣金额

**用途**：
- 用于计算 finalAmount: `finalAmount = originalPrice.subtract(discountAmount)`

**数据流路径**：
```
product.price → originalPrice ──┐
                                ├→ multiply → discountAmount → subtract → finalAmount
user.discountRate ──────────────┘
```

#### 2. 数据：finalAmount (修改)
**位置**：OrderService.java:48

**来源变化**：
- 修改前：直接使用 originalPrice
- 修改后：originalPrice 减去 discountAmount

**计算**：
- 新增了折扣计算逻辑
- `finalAmount = originalPrice.subtract(discountAmount)`

**用途**：
- 保持不变：设置到订单对象 `order.setFinalAmount(finalAmount)`

**数据流路径**（新）：
```
originalPrice + discountAmount → subtract → finalAmount → order
```

#### 3. 数据：user (新增查询)
**位置**：OrderService.java:46

**来源**：
- 数据库查询：`userRepository.findById(userId)`
- userId 来自方法参数 request.getUserId()

**计算**：
- 不涉及计算，直接查询

**用途**：
- 提取用户折扣率：`user.getDiscountRate()` 用于计算折扣

**数据流路径**：
```
request → getUserId() → userId → DB query → user → getDiscountRate() → discountRate
```

### 数据流变化摘要

**新增数据流**：
- 新增用户查询流：request → userId → user → discountRate
- 新增折扣计算流：originalPrice × discountRate → discountAmount

**修改数据流**：
- finalAmount 计算逻辑：从 `原价` 改为 `原价 - 折扣金额`

**影响范围**：
- 影响方法：OrderService.processOrder()
- 影响数据库查询：新增了 userRepository.findById() 调用
- 影响业务逻辑：订单金额计算增加了折扣功能

### 建议关注点

- **多数据源依赖**：finalAmount 现在依赖 product 和 user 两个数据源，需确保两者都能正确获取
- **复杂计算**：折扣计算涉及 BigDecimal 运算，如需详细了解精度处理，可使用 `/analyze-calculation discountAmount`
```

## 注意事项

1. **仅分析数据流**：关注数据的来源、转换、用途，不评价代码质量
2. **聚焦修改内容**：主要分析 git diff 中的变化，不深入分析未修改的代码
3. **识别关键数据**：自动识别重要的数据实体，忽略日志、注释等无关内容
4. **提供完整上下文**：必要时读取完整文件，确保数据流分析准确
5. **标注变化类型**：明确标注是"新增"还是"修改"
6. **避免过度分析**：如果 diff 很大，关注最重要的数据流变化

## 补充命令

如果用户需要更详细的分析，建议使用：
- `/trace-data-source [变量名]` - 深入追踪特定数据的来源
- `/analyze-calculation [变量名]` - 详细分析计算过程
- `/explain-data-flow [方法名]` - 完整分析某个方法的数据流

## 工具使用优先级

1. **Bash (git)** - 获取当前修改信息
2. **Read** - 读取相关文件完整内容
3. **Grep** - 搜索变量和方法定义
4. **Glob** - 查找相关文件（必要时）

优先分析 git diff 中的变化，避免无关代码的干扰。
