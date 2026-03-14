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
