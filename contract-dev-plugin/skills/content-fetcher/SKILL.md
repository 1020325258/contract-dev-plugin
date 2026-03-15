# Content Fetcher Skill

## 概述

从配置的数据源抓取最新内容，整理并保存为 Markdown 文件。

## 数据源类型与抓取策略

### 博客 (blog)

**优先级策略：**
1. **RSS Feed**（最优）：检查 `/rss.xml`, `/feed.xml`, `/atom.xml`, `/feed`, `/rss`
2. **页面解析**：从首页提取文章链接，获取标题

**支持的网站：**

| 网站 | 方式 | URL |
|------|------|-----|
| Jesse Vincent | RSS | `https://blog.fsck.com/feed/rss.xml` |
| Anthropic Engineering | 页面解析 | `https://www.anthropic.com/engineering` |

### B站 (bilibili)

**方式：** 使用 B站 API

**API 端点：**
```
https://api.bilibili.com/x/space/wbi/arc/search?mid={用户ID}&ps=10&order=pubdate
```

**注意：** B站 API 可能需要签名或 Cookie，如果失败则标记为受限。

### YouTube (youtube)

**方式：** 官方 RSS 或页面解析

**RSS 格式：**
```
https://www.youtube.com/feeds/videos.xml?channel_id={频道ID}
https://www.youtube.com/feeds/videos.xml?user={用户名}
```

**注意：** YouTube 可能需要特定网络环境访问。

## 执行流程

```
1. 读取配置文件
2. 遍历每个数据源
3. 根据类型选择抓取策略：
   - blog: 尝试 RSS → 页面解析
   - bilibili: API → 标记受限
   - youtube: RSS → 页面解析 → 标记受限
4. 为每条内容生成摘要
5. 汇总结果，按类型分组
6. 保存为 Markdown 文件
```

## 摘要生成

对于每条内容，生成简短摘要（1-2 句话）。

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

---

## 抓取状态

| 数据源 | 状态 | 备注 |
|--------|------|------|
| ... | ✅/❌ | ... |
```

## 错误处理

- 如果某个源抓取失败，记录错误但继续处理其他源
- 在输出文件中标注抓取失败的源
- 提供备用方案建议

## 网络请求工具

使用 Python urllib 进行网络请求：

```python
import urllib.request
import ssl

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

req = urllib.request.Request(url, headers={
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
})
response = urllib.request.urlopen(req, context=ctx, timeout=15)
content = response.read().decode('utf-8')
```
