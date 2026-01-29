# Contract Dev Plugin

专业的签约系统代码开发辅助插件，提供代码审查、数据流追踪和开发规范指导功能。

## 功能特性

### 1. `/code-review` 命令 - 专业代码审查

对指定的代码文件或代码片段进行全面的 Code Review，特别针对签约项目的代码规范进行审查。

**审查维度**：
- **代码质量**: 检查代码的可读性、可维护性和代码风格
- **空指针安全**: 重点检查 `contractReq.getPromiseInfo()` 等可能返回 null 的方法是否使用 `Optional` 包装
- **潜在问题**: 识别可能的 bug、逻辑错误、边界条件处理不当等问题
- **性能优化**: 发现性能瓶颈和优化建议
- **最佳实践**: 建议更符合行业标准和设计模式的实现方式

**输出格式**：
- 审查概览（文件路径、代码行数、严重程度）
- 通过的检查项
- 需要改进的地方（中等优先级）
- 严重问题（必须修复）
- 代码质量评分
- 改进建议（短期/中期/长期）

**用法**：
```bash
# 审查指定文件
/code-review src/service/ContractService.java

# 审查多个文件
/code-review src/service/*.java

# 审查代码片段（在对话中粘贴代码后）
/code-review
```

### 2. `/trace-data-source` 命令 - 追踪数据来源

深入追踪指定变量或方法的完整来源链路，帮助理解数据的原始来源和传递路径。

**适用场景**：
- 调试时需要知道变量从哪里来
- 理解方法参数的原始数据源
- 追踪合同 PDF 字段的数据来源
- 了解数据库查询结果的使用路径

**用法示例**：
```bash
# 追踪变量来源
/trace-data-source userName
/trace-data-source finalAmount

# 追踪指定文件和行号的数据
/trace-data-source ContractService.java:45

# 追踪方法的数据来源
/trace-data-source getStructureInfo
```

### 3. `/dev-help` 命令 - 开发规范指导

基于签约系统的开发规范，提供开发指导和代码示例。

**当前支持的规范**：
- **文件上传 S3**: 如何上传文件到 S3，获取临时或永久 URL
- **合同 PDF 数据构建**: 理解 `ContractPdfBuildService` 类的数据流向

**用法**：
```bash
# 调用开发规范指导
/dev-help

# 或者直接在对话中询问
如何上传文件到 S3？
合同 PDF 的字段数据从哪里来？
```

### 4. `data-flow-tracer` Agent - 数据流追踪助手

专门处理数据流分析任务的自动化 Agent，当你询问数据相关问题时会自动触发。

**自动触发场景**：
- "这个变量从哪来？"
- "如何计算这个值？"
- "数据是怎么流动的？"
- "合同 PDF 的 XXX 字段来源是什么？"
- "为什么这里会返回 null？"

### 5. Skills 自动调用

插件包含多个 Skills，会根据上下文自动调用：

#### `code-review` Skill
签约项目代码审查规范，重点检查：
- 空指针安全（`Optional` 使用）
- `contractReq.getPromiseInfo()` 等关键方法的 null 检查
- 常见的空指针异常风险

#### `code-knowledge` Skills
签约系统开发知识库，包括：

**contract-pdf-build-service**
- `ContractPdfBuildService` 类的知识库
- 理解合同 PDF 字段的数据来源
- 通过 `result.put(key, value)` 追踪数据流向

**file-upload-s3**
- 文件上传 S3 的代码规范
- 获取临时 URL（15天过期）
- 获取永久 URL 的方法

## 安装使用

### 安装插件

将此插件目录放置在 Claude Code 的插件目录中，插件会自动被加载。

### 快速开始

插件的大部分功能会根据你的对话内容自动触发，无需手动调用。

#### 代码审查

```bash
# 使用命令审查代码
/code-review src/service/ContractService.java

# 或者在对话中直接询问
请帮我审查这个类的代码
```

#### 数据流追踪

```bash
# 使用命令追踪数据
/trace-data-source userName

# 或者在对话中直接询问
这个 finalAmount 变量是从哪里来的？
合同 PDF 的结构信息字段来源是什么？
```

#### 开发规范指导

```bash
# 使用命令获取开发规范
/dev-help

# 或者在对话中直接询问
如何上传文件到 S3？
如何获取永久的 PDF URL？
```

#### 自动触发示例

以下问题会自动触发相应的功能：

**代码审查**
- "帮我审查这段代码"
- "这段代码有什么问题？"
- "检查一下空指针安全"

**数据流追踪**
- "这个变量从哪来？"
- "为什么这里会是 null？"
- "合同 PDF 的 XXX 字段来源"

**开发规范**
- "如何上传文件到 S3？"
- "怎么获取永久 URL？"
- "PDF 数据是如何构建的？"

## 插件配置

插件配置文件位于 `.claude-plugin/plugin.json`：

```json
{
  "name": "contract-dev-plugin",
  "description": "代码开发辅助插件，包含代码审查、代码解释和数据流分析功能",
  "version": "2.0.0",
  "author": {
    "name": "11来了"
  },
  "commands": [
    "./commands/code-review.md",
    "./commands/trace-data-source.md",
    "./commands/dev-help.md"
  ],
  "skills": [
    "./skills/code-review",
    "./skills/code-knowledge"
  ]
}
```

## 目录结构

```
contract-dev-plugin/
├── .claude-plugin/
│   └── plugin.json                          # 插件配置文件
├── commands/
│   ├── code-review.md                       # 代码审查命令
│   ├── trace-data-source.md                 # 追踪数据来源命令
│   └── dev-help.md                          # 开发规范指导命令
├── skills/
│   ├── code-review/                         # 代码审查规范
│   │   └── SKILL.md
│   └── code-knowledge/                      # 开发知识库
│       ├── contract-pdf-build-service.md    # 合同 PDF 构建服务知识
│       └── file-upload-s3.md                # S3 文件上传规范
├── agents/
│   └── data-flow-tracer.md                  # 数据流追踪助手 agent
└── README.md                                # 本文档
```

## 使用示例

### 示例 1: 代码审查

**场景**: 审查签约服务代码

```bash
/code-review src/service/ContractService.java
```

**输出示例**:
```
### 📋 审查概览
- **审查文件**: src/service/ContractService.java
- **代码行数**: 234
- **审查时间**: 2026-01-29
- **严重程度**: 🔴高危

### ✅ 通过的检查项
- 代码结构清晰，职责分明
- 命名规范符合标准

### ⚠️ 需要改进的地方

#### 1. 建议使用更明确的异常处理
- **位置**: ContractService.java:56
- **建议**: 捕获具体的异常类型而不是 Exception

### ❌ 严重问题（必须修复）

#### 🔴 1. 未使用 Optional 包装可能为 null 的数据
- **位置**: ContractService.java:89
- **问题**: 直接调用 contractReq.getPromiseInfo() 未使用 Optional 包装
- **风险**: 可能导致 NullPointerException
- **修复建议**:
  ```java
  // 修改前
  PromiseInfo info = contractReq.getPromiseInfo();
  String name = info.getName();

  // 修改后
  String name = Optional.ofNullable(contractReq.getPromiseInfo())
      .map(PromiseInfo::getName)
      .orElse("");
  ```

### 📊 代码质量评分
- **总分**: 65/100
- **安全性**: 45/100 ⚠️
- **可维护性**: 75/100
- **性能**: 70/100
```

### 示例 2: 追踪数据来源

**场景**: 想知道合同 PDF 中某个字段的数据来源

```bash
/trace-data-source structure
```

或者直接询问：
```
合同 PDF 中的 structure 字段是从哪里来的？
```

**输出示例**:
```
📊 数据流追踪: structure

数据来源分析：

1️⃣ 数据定义位置
- 文件: ContractPdfBuildService.java:26
- 方法: getStructureInfo()
- 通过 result.put("structure", value) 传入合同 PDF

2️⃣ 原始数据来源
- ContractContextHandler.getContractReq().getProjectInfo().getStructure()
- 数据类型: String (枚举值)

3️⃣ 数据转换过程
- 获取原始枚举值: projectInfo.getStructure()
- 转换为名称: StructureEnum.getNameByCode(code)
- 使用 Optional 处理空值: orElse("")

4️⃣ 数据流向图
ContractReq
  └─> ProjectInfo
      └─> structure (枚举值)
          └─> StructureEnum.getNameByCode()
              └─> result.put("structure", name)
                  └─> 合同 PDF 模板
```

### 示例 3: 开发规范指导

**场景**: 需要上传文件到 S3

```bash
/dev-help
```

或者直接询问：
```
如何上传文件到 S3 并获取永久 URL？
```

**输出示例**:
```
📚 S3 文件上传规范

上传文件并获取永久 URL 的标准流程：

1️⃣ 引入依赖
```java
@Resource
private S3Service s3Service;
@Resource
private ContractPdfFileHandleService contractPdfFileHandleService;
```

2️⃣ 生成文件 key
```java
// PDF 文件使用 .pdf 后缀，图片使用 .jpg 后缀
String fileKey = "file_unique_key" + "_" + UUID.randomUUID() + ".pdf";
```

3️⃣ 上传 S3（临时 URL，15天过期）
```java
String fileUrl = s3Service.getMediaUrl(fileKey, 15 * 24 * 60 * 60);
```

4️⃣ 转换为永久 URL
```java
String permanentUrl = contractPdfFileHandleService.convertToPermanentUrl(fileUrl);
```

⚠️ 注意事项：
- 临时 URL 默认 15 天过期
- 需要永久保存的文件必须调用转换方法
- 文件 key 需要保证唯一性
```

## 开发与扩展

### 添加新的开发规范

如果需要添加新的开发规范知识，可以在 `skills/code-knowledge/` 目录下创建新的 markdown 文件。

**文件格式**:
```markdown
---
name: new-knowledge
description: 新的开发知识描述，用于说明何时使用此知识
---

# 知识标题

## 使用场景
说明什么情况下需要参考这个知识

## 代码示例
提供实际的代码示例

## 注意事项
列出关键注意点
```

**示例**:

创建文件 `skills/code-knowledge/contract-approval-flow.md`：

```markdown
---
name: contract-approval-flow
description: 合同审批流程的代码规范，用于理解合同审批相关的业务逻辑
---

# 合同审批流程规范

## 使用场景
当需要处理合同审批相关的功能时参考此规范

## 审批状态枚举
```java
public enum ApprovalStatus {
    PENDING,    // 待审批
    APPROVED,   // 已通过
    REJECTED    // 已拒绝
}
```

## 注意事项
- 审批状态变更需要记录操作日志
- 需要发送审批通知
```

然后在 `/dev-help` 命令中添加引用：

```markdown
## 开发规范
文件上传 S3：./skills/code-knowledge/file-upload-s3.md
合同审批流程：./skills/code-knowledge/contract-approval-flow.md
```

### 自定义代码审查规则

可以修改 `skills/code-review/SKILL.md` 来调整代码审查的规则和重点检查项。

### 添加新命令

在 `commands/` 目录下创建新的命令文件，并在 `plugin.json` 中注册：

```json
{
  "commands": [
    "./commands/code-review.md",
    "./commands/trace-data-source.md",
    "./commands/dev-help.md",
    "./commands/your-new-command.md"
  ]
}
```

## 核心特性

### 智能化
- 自动识别对话意图，无需记忆命令
- 根据上下文自动调用合适的 Skills 和 Agent
- 提供符合签约系统特点的专业建议

### 专业性
- 针对签约系统的特定场景优化
- 重点关注空指针安全等关键问题
- 提供实际的代码示例和最佳实践

### 高效性
- 快速定位数据来源和流向
- 准确的代码审查和问题识别
- 开发规范即查即用

## 适用场景

本插件特别适用于以下开发场景：

1. **新人上手签约系统**: 快速了解代码规范和常用开发模式
2. **代码审查**: 提高代码质量，减少空指针等常见问题
3. **问题调试**: 快速追踪数据来源，定位问题根因
4. **功能开发**: 参考标准规范，避免重复造轮子
5. **知识沉淀**: 将团队的最佳实践固化到插件中

## 版本历史

### v2.0.0 (2026-01-29)
- ✨ 新增 `data-flow-tracer` Agent，支持智能数据流追踪
- ✨ 新增 `/trace-data-source` 命令，快速追踪数据来源
- ✨ 新增 `/dev-help` 命令，提供开发规范指导
- ✨ 新增 `code-knowledge` Skills，包含 S3 上传和 PDF 构建知识
- 🔧 优化代码审查规范，更贴合签约系统特点
- 📝 完善文档和使用示例

### v1.0.0 (2026-01-17)
- 🎉 初始版本发布
- ✨ 支持 `/code-review` 命令
- ✨ 包含签约项目代码审查规范

## 后续规划

- [ ] 支持更多签约系统的开发规范（审批流程、权限控制等）
- [ ] 增强数据流追踪的可视化展示
- [ ] 支持批量代码审查和报告生成
- [ ] 添加常见问题解决方案库
- [ ] 集成单元测试生成功能

## 贡献指南

欢迎贡献新的开发规范和使用案例！

1. Fork 本项目
2. 创建特性分支 (`git checkout -b feature/new-knowledge`)
3. 在 `skills/code-knowledge/` 添加新的知识文档
4. 提交变更 (`git commit -m 'Add new knowledge'`)
5. 推送到分支 (`git push origin feature/new-knowledge`)
6. 创建 Pull Request

## 作者

**11来了**

## 许可证

MIT License

## 联系与支持

如有问题或建议，欢迎：
- 提交 Issue
- 发起 Pull Request
- 联系项目维护者
