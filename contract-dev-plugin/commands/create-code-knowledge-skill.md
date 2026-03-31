---
description: 将开发经验持久化为 skill 文档，采用三层知识架构，支持动态 skill 发现和新 skill 创建。
argument-hint: "[指定要写入的内容]"
allowed-tools: Read, Write, Edit, Grep, Glob
---

## 职责

按照**三层知识架构**，将开发经验写入对应位置，确保：
1. 顶层 `SKILL.md` 仅作为**导航索引**，不嵌入完整内容
2. 具体知识按层级分目录存放在 `references/` 下
3. 三层结构帮助 agent 快速判断知识的重要性和用途
4. 支持动态发现已有 skill 和创建新 skill

## 插件源码目录

`/Users/zqy/work/AI-Project/claude-code-plugins/sales-project-plugins/contract-dev-plugin/`

---

## 三层知识架构

```
skills/<skill-name>/
├── SKILL.md                      # 顶层索引（仅导航，不嵌入内容）
└── references/
    ├── foundation/               # 基础层：每次开发必须具备的知识
    │   ├── core-concepts.md      # 核心概念、术语定义
    │   └── database-schema.md    # 数据库表结构 DDL（业务系统）
    ├── domain/                   # 领域层：特定功能开发时需要的知识
    │   ├── business-rules.md     # 业务流程规则（业务系统）
    │   ├── api-reference.md      # API 参考（技术框架）
    │   └── best-practices.md     # 最佳实践
    └── experience/               # 实践经验层：踩坑记录、反直觉的配置陷阱
        ├── troubleshooting.md    # 故障排查
        └── pitfalls.md           # 踩坑记录
```

### 各层定义

| 层级 | 目录 | 内容定性 | 判断标准 |
|------|------|---------|---------|
| **基础层** | `references/foundation/` | 核心概念、DDL、基础配置 | 缺少这些知识，开发会产生根本性误解 |
| **领域层** | `references/domain/` | 业务规则、API 用法、开发指南 | 特定功能开发才需要，不是每次都用 |
| **实践经验层** | `references/experience/` | 踩坑记录、故障排查、反直觉配置 | 仅靠读代码无法发现，需要亲历才知道 |

### 不同类型系统的分层示例

**业务系统（如签约系统）**：

| 内容 | 层级 |
|------|------|
| 核心领域概念（报价单、合同、S单） | foundation |
| 数据库表结构 DDL | foundation |
| 业务流程规则（撤回、绑定） | domain |
| Apollo 开关配置 | domain |
| Lombok @Slf4j 规范踩坑 | experience |

**技术框架（如 Spring AI Alibaba）**：

| 内容 | 层级 |
|------|------|
| 核心概念（Graph、StateGraph、Checkpoint） | foundation |
| 模块开发指南（Agent Framework、Graph Core） | domain |
| API 参考 | domain |
| 最佳实践 | domain |
| 故障排查（版本兼容、配置陷阱） | experience |

---

## 执行流程

### 步骤 0：动态发现目标 skill

**0.1 扫描已有 skills**

扫描 `skills/` 目录，读取每个 `SKILL.md` 的 frontmatter description：

```
skills/
├── code-developer/SKILL.md       → description: "签约领域代码开发指南..."
├── spring-ai-alibaba-developer/  → description: "Spring AI Alibaba 框架开发指南..."
├── reviewer/SKILL.md             → description: "独立审查阶段..."
└── ...
```

**0.2 语义匹配**

将用户输入的内容与各 skill description 进行语义匹配：

- **匹配规则**：内容主题与 description 描述的领域/功能高度相关
- **匹配成功**：进入步骤 1，使用匹配的 skill
- **多个匹配**：列出候选，询问用户选择
- **无匹配**：进入步骤 0.3

**0.3 无匹配时的处理**

询问用户：

> 未找到匹配的已有 skill，请选择：
> 1. 写入已有 skill（列出选项）
> 2. 创建新 skill

若选择创建新 skill，进入步骤 0.4。

**0.4 创建新 skill**

引导用户提供以下信息：

| 字段 | 说明 | 示例 |
|------|------|------|
| skill 名称 | 小写连字符格式 | `spring-ai-alibaba-developer` |
| description | 一句话描述 skill 的用途 | "Spring AI Alibaba 框架开发指南，包含架构理解、系统设计和功能开发指导" |

创建 skill 骨架：

```
skills/<skill-name>/
├── SKILL.md
└── references/
    ├── foundation/
    ├── domain/
    └── experience/
```

SKILL.md 模板：

```markdown
---
description: <用户提供的一句话描述>
---

# <Skill 标题>

## 知识索引

### 基础层（必读）
<!-- 核心概念、必知术语 -->

### 领域层（按需查阅）
<!-- 开发指南、API 参考、最佳实践 -->

### 实践经验层（遇到问题时查阅）
<!-- 踩坑记录、故障排查 -->
```

创建完成后，进入步骤 1。

---

### 步骤 1：确定知识层级与目标目录

根据内容特征，选择对应层级：

| 内容特征 | 层级 | 目标目录 |
|---------|------|---------|
| 核心概念、术语定义、必知基础知识 | 基础层 | `references/foundation/` |
| 数据库 DDL、表结构、字段含义 | 基础层 | `references/foundation/` |
| 业务流程规则、领域逻辑 | 领域层 | `references/domain/` |
| API 用法、开发指南、最佳实践 | 领域层 | `references/domain/` |
| Apollo 开关配置、Feature Flag | 领域层 | `references/domain/` |
| 技术实现规范（RPC、分布式锁） | 领域层 | `references/domain/` |
| 踩坑记录、故障排查 | 实践经验层 | `references/experience/` |
| 版本兼容性问题、配置陷阱 | 实践经验层 | `references/experience/` |
| 环境问题、启动失败排查 | 实践经验层 | `references/experience/` |

**边界判断**：
- 有业务规则但同时是基础概念 → 优先归入基础层
- 技术实现规范 → 判断是否每次开发都需要：是 → 基础层；否 → 领域层

---

### 步骤 2：检索是否已有相关内容

- 扫描目标子目录下所有 `.md` 文件
- 判断文件主题是否与本次经验相关
- **命中** → 进入步骤 3（修改现有文件）
- **未命中** → 进入步骤 4（新建文件）

---

### 步骤 3：已有相关内容 — 定位修改

- 找到相关段落，在原有位置补充或完善
- **不改变文件整体结构**
- 完成后跳至步骤 5

---

### 步骤 4：无相关内容 — 新建文件并更新索引

**4.1 创建知识文件**

- 在目标子目录下新建语义明确的 `.md` 文件
- 文件命名规则：`<主题关键词>.md`（小写，连字符分隔）

**4.2 更新 SKILL.md 索引**

在 `SKILL.md` 对应层级分组下添加导航条目：

```markdown
### 基础层（必读）
- [主题标题](./references/foundation/<文件名>.md) - 一句话描述

### 领域层（按需查阅）
- [主题标题](./references/domain/<文件名>.md) - 一句话描述

### 实践经验层（遇到问题时查阅）
- [主题标题](./references/experience/<文件名>.md) - 一句话描述
```

**索引条目要求**：
- 标题清晰，能准确反映内容主题
- 描述简洁，一句话说明"何时需要查阅此文档"
- 基础层条目排在最前，实践经验层排在最后

---

### 步骤 5：同步更新 plugin.json 版本

- 路径：`/Users/zqy/work/AI-Project/claude-code-plugins/sales-project-plugins/contract-dev-plugin/.claude-plugin/plugin.json`
- 对 `version` 字段做 patch 版本升级（如 `1.8.5` → `1.8.6`）

---

## 写入格式

### 知识文件模板

```markdown
# [主题标题]

## 概述
<!-- 一句话说明本文档解决的问题 -->

## 背景
<!-- 必要的上下文信息 -->

## 核心内容
<!-- 具体内容：概念定义 / 配置项 / 业务规则 / 踩坑过程 -->

## 注意事项
<!-- 易错点、边界条件 -->

## 相关链接
<!-- 关联的其他知识文档 -->
```

### 索引条目模板（SKILL.md 中）

```markdown
- [标题](./references/<层级目录>/<文件>.md) - 简要描述
```

---

## 写入原则

### 渐进式披露原则

**SKILL.md 只做导航，不嵌入完整内容**：
- ✅ 正确：在 SKILL.md 中放索引链接 + 一句话描述
- ❌ 错误：在 SKILL.md 中直接写完整流程

**判断标准**：
- 如果内容超过 3 行，就应该放入 references 文件
- SKILL.md 的单个条目描述不超过 1 行

### 简洁性原则

遵循奥卡姆剃刀原则：
- ✅ 只写 Claude Code 无法通过工具推断的特定领域知识
- ❌ 禁止写入：Service/Repository 方法列表、标准 CRUD 说明、可从代码结构直接推断的信息

**必要性测试**：
- 如果不添加这个内容，Claude 是否会误解业务逻辑？
- 答案是"不会"或"可能不会" → 不写

### 准确性原则

- `背景` 没有十足把握不要修改
- 强制阅读相关领域知识文档，保证术语对齐
- 解释枚举含义时，务必读取枚举类源码，不能凭命名推测

---

## 示例

### 基础层文件示例（业务系统）

```markdown
# 核心领域概念

## 概述
签约系统的核心业务实体及其关系定义。

## 核心实体

| 实体 | 说明 |
|------|------|
| 报价单 | 客户确认价格后生成的单据，是合同的来源 |
| 合同 | 法律效力文件，由报价单生成 |
| S单 | 销售订单，合同与 S 单绑定后生效 |

## 实体关系
报价单 → 合同 → S单（绑定关系）
```

### 基础层文件示例（技术框架）

```markdown
# Graph 核心概念

## 概述
Spring AI Alibaba 图工作流引擎的核心抽象。

## 核心概念

| 概念 | 说明 |
|------|------|
| Graph | 有向图结构，定义节点和边的拓扑 |
| StateGraph | 携带状态的图，状态在节点间传递 |
| Checkpoint | 图执行状态的持久化快照，支持暂停/恢复 |

## 执行模型
StateGraph 执行时，状态沿边传递，每个节点可读取和修改状态。
```

### 实践经验层文件示例

```markdown
# SSE 流式输出踩坑

## 概述
前端与后端 SSE 对接时遇到的序列化问题。

## 背景
使用 markstream-vue 前端组件对接后端 SSE 接口时，出现 JSON 解析错误。

## 问题原因
Flux 返回的对象需要使用 FluxConverter 序列化，否则前端无法正确解析。

## 解决方案
```java
@GetMapping(value = "/stream", produces = MediaType.TEXT_EVENT_STREAM_VALUE)
public Flux<ServerSentEvent<ChatResponse>> stream(@RequestParam String input) {
    return FluxConverter.toSse(chatService.stream(input));
}
```

## 注意事项
- FluxConverter 是 Spring AI Alibaba 提供的工具类
- 双消息类型设计需要前端配合处理
```

### 索引条目示例（SKILL.md 中）

```markdown
### 基础层（必读）
- [核心领域概念](./references/foundation/domain-concepts.md) - 报价单、合同、S单等核心术语定义

### 领域层（按需查阅）
- [Apollo 开关配置](./references/domain/apollo-switches.md) - 影响签约流程的 Apollo 配置项
- [API 参考](./references/domain/api-reference.md) - Graph API 完整参考

### 实践经验层（遇到问题时查阅）
- [SSE 流式输出踩坑](./references/experience/sse-streaming-pitfall.md) - 前后端 SSE 对接序列化问题
```

---

## 迁移指南

对于使用旧版目录结构（domain/technical/workflow/infrastructure）的 skill，执行以下迁移：

| 旧目录 | 内容特征 | 迁移到 |
|--------|---------|--------|
| `infrastructure/` | DDL、数据库表结构 | `foundation/` |
| `domain/` 中的核心概念文件 | 基础术语、必知模型 | `foundation/` |
| `domain/` 中的流程规则文件 | 具体业务流程、配置 | `domain/` |
| `technical/` | 技术规范（RPC/锁/上传等） | `domain/` |
| `workflow/` | 踩坑、排查问题、测试工具 | `experience/` |

迁移步骤：
1. 在目标层级目录下新建文件（或直接移动文件）
2. 更新 SKILL.md 中的索引链接路径
3. 删除旧目录下的空目录
