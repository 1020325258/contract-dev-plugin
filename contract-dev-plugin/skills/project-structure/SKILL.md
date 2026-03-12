---
description: 项目结构规范，指导 DDD 单体项目的包结构设计，适用于新项目初始化和存量项目重构。
---

# 项目结构规范

## 核心原则

### 原则一：层级职责单一

每一层只放本层职责的类，严禁跨层放置。

| 层级 | 允许放置的类 | 典型违规 |
|------|------------|--------|
| `trigger/` | Controller、@Tool、EventListener、Consumer | 把 Gateway 实现放进 trigger |
| `domain/` | 领域模型、领域服务、Gateway 接口 | 把业务逻辑写在 infrastructure |
| `infrastructure/` | Gateway 实现、持久化、外部调用、技术组件 | 把技术实现放在 domain |

**判断标准**：新建一个类时，先问"它是入口？是业务逻辑？还是技术实现？"——答案决定它属于哪一层。

---

### 原则二：Package 名如实反映内容

Package 名 = 包内所有类共同的技术关注点。当包内出现与名称不符的类时，是拆分的信号。

```
❌ infrastructure/service/
   ├── CacheService.java        # 服务
   ├── DirectOutputHolder.java  # 状态持有器，不是服务
   ├── ToolResult.java          # 工具类，不是服务
   └── MetricsCollector.java    # 监控，不是服务

✅ infrastructure/
   ├── agent/          # Agent 执行机制（Holder、Template、Result）
   ├── observability/  # 可观测性（Metrics、Tracing）
   └── service/        # 服务（只放 Service 类）
```

---

### 原则三：禁止单类 Package

不应为单个类创建独立 package，同一子系统的相关类应放在一起。

```
❌
infrastructure/
  loader/
    KnowledgeLoader.java     # 一个包只有一个类
  properties/
    KnowledgeProperties.java # 一个包只有一个类

✅
infrastructure/
  knowledge/
    KnowledgeLoader.java
    KnowledgeProperties.java
```

**判断标准**：如果这个包未来很可能只有这一个类，就合并到上层或相邻包。

---

### 原则四：Infrastructure 内按技术关注点子分包

`infrastructure/` 内部按职责拆分子包，粒度以"同一技术关注点"为准，不要过细也不要全堆在 `service/`。

**常见子包划分参考**：

| 子包 | 放置内容 |
|------|---------|
| `gateway/` | 领域 Gateway 接口的实现类 |
| `config/` | `@Configuration`、`@ConfigurationProperties` |
| `agent/` | AI Agent 执行机制相关组件 |
| `observability/` | 指标收集、链路追踪 |
| `cache/` | 缓存实现（如果足够独立） |
| `util/` | 无状态纯静态工具方法 |
| `service/` | 其余通用基础设施服务 |

**粒度原则**：2 个以上类共享同一技术关注点，才值得单独建子包。

---

## 新项目初始化检查清单

开始新项目时，在写第一行业务代码前确认：

- [ ] `trigger/` 只有入口类，无业务逻辑、无技术实现
- [ ] `infrastructure/` 按技术关注点拆分子包，无单类包
- [ ] `infrastructure/service/` 内只有 Service 类
- [ ] `@ConfigurationProperties` 放在 `infrastructure/config/`，不单独建包
- [ ] Gateway 实现类放在 `infrastructure/gateway/`，不放在 `trigger/`
