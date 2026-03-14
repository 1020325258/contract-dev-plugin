# Content Fetcher Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 在 contract-dev-plugin 中添加 `/fetch-updates` 命令，用于获取博客和视频网站的最新内容并保存为本地 Markdown 文件。

**Architecture:** 创建一个命令入口 `fetch-updates.md` 和核心技能 `content-fetcher/SKILL.md`，使用 WebFetch 工具抓取网站内容，Claude 生成摘要，结果保存为 Markdown 文件。

**Tech Stack:** Claude Code Plugin（命令 + 技能）、WebFetch 工具、Markdown 输出

---

## Task 1: 创建数据源配置文件

**Files:**
- Create: `.claude-plugin/content-sources.json`

**Step 1: 创建配置文件**

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
      "type": "bilibili",
      "name": "B站UP主2",
      "space_id": "1815948385"
    },
    {
      "type": "youtube",
      "name": "DLCorner",
      "channel": "@dlcorner"
    },
    {
      "type": "youtube",
      "name": "YC-more",
      "channel": "@YC-more"
    }
  ],
  "output_dir": "~/content-updates"
}
```

**Step 2: 提交**

```bash
cd /Users/zqy/work/AI-Project/claude-code-plugins/sales-project-plugins/contract-dev-plugin
git add .claude-plugin/content-sources.json
git commit -m "feat: add content-sources config for fetch-updates command"
```

---

## Task 2: 创建 content-fetcher 技能

**Files:**
- Create: `skills/content-fetcher/SKILL.md`

**Step 1: 创建技能目录和文件**

```markdown
# Content Fetcher Skill

## 概述

从配置的数据源抓取最新内容，整理并保存为 Markdown 文件。

## 数据源类型

### 博客 (blog)

使用 WebFetch 抓取博客首页或 RSS feed，提取最新文章信息。

**抓取策略：**
1. 尝试访问 RSS feed（如 `/rss`, `/feed`, `/atom.xml`）
2. 若无 RSS，访问首页解析文章列表
3. 提取标题、链接、发布时间

**Anthropic Engineering 特殊处理：**
- URL: `https://www.anthropic.com/engineering`
- 页面结构：查找文章卡片，提取标题和链接

**blog.fsck.com 特殊处理：**
- URL: `https://blog.fsck.com/`
- 可能是 Movable Type 博客，查找最新文章列表

### B站 (bilibili)

使用 WebFetch 访问 UP 主空间页面。

**URL 格式：** `https://space.bilibili.com/{space_id}`

**提取信息：**
- 视频标题
- 视频链接
- 发布时间
- 播放量（可选）

### YouTube (youtube)

使用 WebFetch 访问频道页面。

**URL 格式：** `https://www.youtube.com/{channel}`

**提取信息：**
- 视频标题
- 视频链接
- 发布时间

## 摘要生成

对于每条内容，使用以下 prompt 生成摘要：

```
请用 1-2 句话总结以下内容的核心要点：
标题：{title}
内容：{content_snippet}
```

## 输出格式

保存为 `~/content-updates/YYYY-MM-DD.md`：

```markdown
# 内容更新 - YYYY-MM-DD

## 📝 博客文章

### [{source_name}] {title}
- 发布时间：{publish_date}
- 链接：{url}
- 摘要：{summary}

## 🎬 视频内容

### [{platform} - {creator}] {title}
- 发布时间：{publish_date}
- 链接：{url}
- 摘要：{summary}
```

## 执行流程

1. 读取 `.claude-plugin/content-sources.json` 配置
2. 遍历每个数据源
3. 使用 WebFetch 抓取页面内容
4. 解析提取最新内容（每个源最多 3-5 条）
5. 为每条内容生成摘要
6. 汇总结果，按类型分组
7. 保存为 Markdown 文件

## 错误处理

- 如果某个源抓取失败，记录错误但继续处理其他源
- 在输出文件中标注抓取失败的源
```

**Step 2: 提交**

```bash
cd /Users/zqy/work/AI-Project/claude-code-plugins/sales-project-plugins/contract-dev-plugin
git add skills/content-fetcher/SKILL.md
git commit -m "feat: add content-fetcher skill"
```

---

## Task 3: 创建 fetch-updates 命令

**Files:**
- Create: `commands/fetch-updates.md`

**Step 1: 创建命令文件**

```markdown
---
description: 获取博客和视频网站的最新内容，保存为本地 Markdown 文件
allowed-tools: Read, Write, WebFetch, Bash(mkdir:*), Bash(ls:*)
---

## 配置文件

读取配置：`${CLAUDE_PLUGIN_ROOT}/.claude-plugin/content-sources.json`

## 任务

使用 **content-fetcher** Skill 完成以下步骤：

### 1. 读取配置

读取数据源配置文件，获取需要抓取的网站列表。

### 2. 创建输出目录

确保 `~/content-updates` 目录存在。

### 3. 抓取各数据源最新内容

对于每个数据源：

**博客类：**
- 使用 WebFetch 访问网站
- 提取最新 3-5 篇文章的标题、链接、发布时间
- 为每篇文章生成简短摘要

**B站：**
- 使用 WebFetch 访问 `https://space.bilibili.com/{space_id}`
- 提取最新 3-5 个视频的标题、链接、发布时间

**YouTube：**
- 使用 WebFetch 访问 `https://www.youtube.com/{channel}`
- 提取最新 3-5 个视频的标题、链接、发布时间

### 4. 整理并保存

将所有内容按类型分组，保存为 Markdown 文件：

- 文件路径：`~/content-updates/YYYY-MM-DD.md`
- 格式：参见 content-fetcher Skill 中的输出格式

### 5. 输出摘要

完成后，在终端输出简要摘要：
- 共抓取了多少个源
- 共获取了多少条内容
- 文件保存路径
```

**Step 2: 提交**

```bash
cd /Users/zqy/work/AI-Project/claude-code-plugins/sales-project-plugins/contract-dev-plugin
git add commands/fetch-updates.md
git commit -m "feat: add fetch-updates command"
```

---

## Task 4: 更新 plugin.json 注册新组件

**Files:**
- Modify: `.claude-plugin/plugin.json`

**Step 1: 更新 plugin.json**

将 `commands` 和 `skills` 数组更新为：

```json
{
  "name": "contract-dev-plugin",
  "description": "签约系统代码开发辅助插件",
  "version": "1.5.0",
  "author": {
    "name": "11来了"
  },
  "commands": [
    "./commands/code-developer.md",
    "./commands/code-reader.md",
    "./commands/code-review.md",
    "./commands/trace-data-source.md",
    "./commands/create-code-knowledge-skill.md",
    "./commands/fetch-updates.md"
  ],
  "skills": [
    "./skills/code-review",
    "./skills/code-developer",
    "./skills/test-driven-development",
    "./skills/project-structure",
    "./skills/content-fetcher"
  ]
}
```

**Step 2: 提交**

```bash
cd /Users/zqy/work/AI-Project/claude-code-plugins/sales-project-plugins/contract-dev-plugin
git add .claude-plugin/plugin.json
git commit -m "feat: register fetch-updates command and content-fetcher skill in plugin.json"
```

---

## Task 5: 验证功能

**Step 1: 重新加载插件**

在 Claude Code 中重新加载插件配置。

**Step 2: 测试命令**

运行 `/fetch-updates` 命令，验证：
- 配置文件正确读取
- 各数据源能够抓取
- Markdown 文件正确生成

**Step 3: 检查输出文件**

确认 `~/content-updates/YYYY-MM-DD.md` 文件存在且格式正确。
