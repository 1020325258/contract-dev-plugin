# Spring AI Skill 能力

## 概述

Spring AI Skill 是 Anthropic 提出的 Agent 能力扩展机制，允许将特定领域的 SOP（标准操作流程）、工具集合封装为可复用的 Skill。LLM 可以根据用户问题主动感知并调用对应 Skill。

## 核心概念

### Skill 文件结构

```
skills/<skill-name>/
├── SKILL.md                    # 顶层索引（YAML frontmatter + Markdown 指令）
└── references/                 # 详细文档（可选）
```

### SKILL.md 格式

```yaml
---
name: skill-name
description: 一句话描述用途，LLM 用于判断何时调用此 Skill
groupedTools:                   # 可选：Skill 专属工具
  - tool-name-1
  - tool-name-2
---

# Skill 标题

## Instructions
详细的使用说明，LLM 会按此指令执行

## Example
用户: "xxx"
Action: 按上述步骤执行
```

## 关键组件

### 1. SkillRegistry

技能注册中心，负责扫描和加载 Skill 文件。

```java
// 文件系统扫描
SkillRegistry registry = FileSystemSkillRegistry.builder()
    .projectSkillsDirectory("/path/to/skills")
    .build();

// ClassPath 扫描
SkillRegistry registry = ClasspathSkillRegistry.builder()
    .projectSkillsDirectory("skills")
    .build();
```

**源码位置**: `com.alibaba.cloud.ai.graph.skills.registry.*`

### 2. SkillsInterceptor / SkillsAgentHook

将 Skill 注入到 Agent 的 System Prompt。

```java
// 推荐方式：通过 Hook 自动注册
SkillsAgentHook hook = SkillsAgentHook.builder()
    .skillRegistry(registry)
    .autoReload(true)
    .build();
```

**核心机制**:
- 注入 Skills 列表（name + description）
- 注入 `read_skill` 工具
- LLM 可主动调用 `read_skill` 读取完整 Skill 内容

### 3. read_skill 工具

LLM 用于读取 Skill 完整内容的工具。

```java
// 工具定义
ToolCallback readSkillTool = ReadSkillTool.createReadSkillToolCallback(
    skillRegistry,
    "Reads the full content of a skill from the SkillRegistry."
);

// 参数
class ReadSkillRequest {
    String skillName;  // 必填，Skill 名称
}
```

## LLM 感知和执行流程

```
┌─────────────────────────────────────────────────────────────┐
│                    LLM Skill 执行流程                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. System Prompt 注入                                      │
│     ├── Available Skills 列表（name + description）          │
│     └── read_skill 工具可用                                 │
│                                                             │
│  2. 用户输入                                                 │
│     "订单 826031210000003581 发起合同没个性化报价，帮我排查"  │
│                                                             │
│  3. LLM 推理                                                │
│     → 这是一个"排查缺失数据"的问题                          │
│     → 需要使用某个 Skill                                     │
│     → 调用 read_skill("missing-personal-quote-diagnosis")  │
│                                                             │
│  4. 返回完整 SKILL.md 内容                                   │
│     → LLM 按指令执行排查步骤                                │
│                                                             │
│  5. 输出结论                                                │
│     → 断点位置 + 可能原因 + 建议操作                         │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## 使用场景

### 场景一：问题排查 SOP

将排查经验固化为 Skill：

```yaml
---
name: missing-personal-quote-diagnosis
description: 排查合同发起时缺少个性化报价的原因
---

# 排查缺失个性化报价

## 触发条件
用户说"合同发起时没有个性化报价"、"缺少个性化报价数据"

## 排查步骤

1. 查询订单下的合同列表
   - ontologyQuery(entity=Order, value={订单号}, queryScope=Contract)

2. 查询合同的签约单据
   - ontologyQuery(entity=Contract, value={合同号}, queryScope=ContractQuotationRelation)

3. 分析数据链
   - 订单有合同？→ 合同有签约单据？→ 签约单据有绑定报价？

4. 输出结论
   - 断点位置 + 可能原因 + 建议操作
```

### 场景二：按需加载工具

通过 `groupedTools` 实现 Skill 专属工具：

```yaml
---
name: pdf-extractor
description: 从 PDF 提取文本和表格数据
groupedTools:
  - pdf_parser
  - table_extractor
---

# PDF 提取 Skill

## Instructions
1. 验证 PDF 文件路径
2. 调用 pdf_parser 提取文本
3. 调用 table_extractor 提取表格
4. 返回结构化结果
```

## 与 @Tool 注解对比

| 维度 | @Tool 注解 | Skill |
|------|-----------|-------|
| 实现方式 | Java 方法 | Markdown 文件 |
| 适用场景 | 数据查询、结构化操作 | 流程/规范/ SOP |
| 灵活性 | 高（代码控制） | 低（Prompt 控制） |
| 维护成本 | 需要改代码 | 只需改 Markdown |
| 工具绑定 | 启动时注册 | 可通过 groupedTools 动态注入 |

## 集成到 Agent

### 方式一：使用 SkillsAgentHook（推荐）

```java
@Bean
public SkillsAgentHook skillsAgentHook(SkillRegistry skillRegistry) {
    return SkillsAgentHook.builder()
        .skillRegistry(skillRegistry)
        .autoReload(true)  // 开发环境启用热加载
        .build();
}
```

### 方式二：手动注册 SkillsInterceptor

```java
SkillsInterceptor interceptor = SkillsInterceptor.builder()
    .skillRegistry(skillRegistry)
    .groupedTools(Map.of(
        "pdf-extractor", List.of(pdfParserTool, tableExtractorTool)
    ))
    .build();
```

## 源码位置

| 组件 | 路径 |
|------|------|
| SkillRegistry | `spring-ai-alibaba-graph-core/.../skills/registry/` |
| SkillsInterceptor | `spring-ai-alibaba-agent-framework/.../agent/interceptor/skills/` |
| SkillsAgentHook | `spring-ai-alibaba-agent-framework/.../agent/hook/skills/` |
| ReadSkillTool | `spring-ai-alibaba-agent-framework/.../agent/hook/skills/` |

## 示例代码

### 测试用例

参考 `spring-ai-alibaba-agent-framework/src/test/java/.../AgentSkillsTest.java`

```java
@Test
public void testSkillsInterceptorEnhancesSystemPrompt() {
    Resource skillsResource = new ClassPathResource("skills");
    SkillRegistry registry = FileSystemSkillRegistry.builder()
        .projectSkillsDirectory(skillsResource)
        .build();

    SkillsAgentHook hook = SkillsAgentHook.builder()
        .skillRegistry(registry)
        .build();

    // 触发 skill 加载
    hook.beforeAgent(state, config).join();

    // 验证加载成功
    assertTrue(registry.size() > 0);
    assertTrue(registry.contains("pdf-extractor"));
}
```

## 最佳实践

1. **渐进式披露**: SKILL.md 只放索引，详细内容放 references/
2. **description 关键**: 精准的 description 帮助 LLM 正确匹配 Skill
3. **groupedTools**: 复杂 Skill 使用分组工具，避免暴露过多工具
4. **热加载**: 开发环境启用 autoReload，修改 Skill 无需重启
