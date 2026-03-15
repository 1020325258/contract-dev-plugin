---
description: 获取博客和视频网站的最新内容，保存为本地 Markdown 文件
allowed-tools: Read, Write, Bash(mkdir:*), mcp__plugin_contract-dev-plugin_content-fetcher__*
---

## 配置文件

读取配置：`${CLAUDE_PLUGIN_ROOT}/.claude-plugin/content-sources.json`

## 任务

使用 MCP Server 提供的工具抓取各数据源最新内容。

### 1. 读取配置

读取数据源配置文件，获取需要抓取的网站列表。

### 2. 创建输出目录

确保 `~/content-updates` 目录存在。

### 3. 抓取各数据源最新内容

使用 MCP 工具抓取：

**博客类：**
- `mcp__plugin_contract-dev-plugin_content-fetcher__fetch_anthropic_blog`
- `mcp__plugin_contract-dev-plugin_content-fetcher__fetch_jesse_blog`

**B站：**
- `mcp__plugin_contract-dev-plugin_content-fetcher__fetch_bilibili_videos`

**YouTube：**
- `mcp__plugin_contract-dev-plugin_content-fetcher__fetch_youtube_videos`

### 4. 整理并保存

将所有内容按类型分组，保存为 Markdown 文件：

- 文件路径：`~/content-updates/YYYY-MM-DD.md`
- 格式如下：

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

### 5. 输出摘要

完成后，在终端输出简要摘要：
- 共抓取了多少个源
- 共获取了多少条内容
- 文件保存路径
