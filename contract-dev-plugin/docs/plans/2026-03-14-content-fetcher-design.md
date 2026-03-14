# 内容订阅工具设计

## 概述

在 contract-dev-plugin 中新增命令 `/fetch-updates`，用于获取博客和视频网站的最新内容，整理后保存为本地 Markdown 文件。

## 需求

- **数据源**：
  - 博客：blog.fsck.com、anthropic.com/engineering
  - B站：316183842、1815948385
  - YouTube：@dlcorner、@YC-more
- **功能**：获取最新发布的内容
- **输出**：标题 + 链接 + 发布时间 + 摘要
- **存储**：保存为本地 Markdown 文件
- **触发方式**：手动触发 + 定时自动运行

## 架构

```
contract-dev-plugin/
├── commands/
│   └── fetch-updates.md        # 命令入口
├── skills/
│   └── content-fetcher/        # 核心技能
│       └── SKILL.md
└── .claude-plugin/
    └── content-sources.json    # 数据源配置（用户自定义）
```

## 组件说明

### 1. 命令：fetch-updates.md

用户入口，定义允许的工具和基本流程：
- 读取数据源配置
- 调用 content-fetcher skill 执行抓取
- 整理结果并保存为 Markdown

### 2. 技能：content-fetcher/SKILL.md

核心逻辑，包含：
- 各网站的抓取策略（使用 WebFetch 工具）
- 内容解析规则
- 摘要生成（利用 Claude）
- 结果格式化

### 3. 配置：content-sources.json

用户可自定义的数据源配置：

```json
{
  "sources": [
    {
      "type": "blog",
      "name": "Jesse Vincent",
      "url": "https://blog.fsck.com/"
    },
    {
      "type": "blog",
      "name": "Anthropic Engineering",
      "url": "https://www.anthropic.com/engineering"
    },
    {
      "type": "bilibili",
      "name": "B站UP主1",
      "space_id": "316183842"
    },
    {
      "type": "youtube",
      "name": "DLCorner",
      "channel": "@dlcorner"
    }
  ],
  "output_dir": "~/content-updates"
}
```

## 数据流

```
用户执行 /fetch-updates
       ↓
读取 content-sources.json
       ↓
遍历每个数据源 → WebFetch 抓取内容
       ↓
解析最新文章/视频信息
       ↓
Claude 生成摘要
       ↓
汇总结果，保存为 Markdown
```

## 输出格式

文件路径：`~/content-updates/YYYY-MM-DD.md`

```markdown
# 内容更新 - 2026-03-14

## 📝 博客文章

### [Anthropic Engineering] 文章标题
- 发布时间：2026-03-13
- 链接：https://...
- 摘要：...

## 🎬 视频内容

### [B站 - UP主名] 视频标题
- 发布时间：2026-03-12
- 链接：https://...
- 摘要：...

### [YouTube - 频道名] 视频标题
- 发布时间：2026-03-11
- 链接：https://...
- 摘要：...
```

## 定时运行

使用 Claude Code 的 `/loop` 命令实现定时任务：

```
/loop 1d /fetch-updates
```

或通过 CronCreate 工具设置定时任务。

## 技术要点

1. **WebFetch 限制**：部分网站可能有反爬机制，需处理抓取失败情况
2. **摘要生成**：利用 Claude 的理解能力从页面内容提取关键信息
3. **去重机制**：可通过记录已抓取内容的 ID 或链接避免重复
4. **增量更新**：可选功能，只获取上次运行后的新内容
