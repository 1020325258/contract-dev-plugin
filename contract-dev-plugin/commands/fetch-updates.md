---
description: 获取博客和视频网站的最新内容，保存为本地 Markdown 文件
allowed-tools: Read, Write, WebFetch, Bash(mkdir:*), Bash(ls:*), Bash(curl:*)
---

## 配置文件

读取配置：`${CLAUDE_PLUGIN_ROOT}/.claude-plugin/content-sources.json`

## ⚠️ 注意事项

本命令需要网络访问权限。如果遇到权限限制：
1. 确保当前会话允许 `curl` 命令
2. 或在允许 WebFetch 访问外部网站的环境中使用

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
