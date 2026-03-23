"""
RSSHub 抓取模块 - 使用 RSSHub JSON API 获取内容
RSSHub 是一个开源项目，可以为各种网站生成 RSS/JSON 订阅
文档: https://docs.rsshub.app/
"""

import json
import ssl
import urllib.request
from typing import Any
from datetime import datetime


# RSSHub 公共实例列表
RSSHUB_INSTANCES = [
    "https://rsshub.app",
    "https://rsshub.rssforever.com",
]


def _fetch_rsshub_json(path: str, timeout: int = 15) -> dict | None:
    """
    从 RSSHub 获取 JSON 数据

    Args:
        path: RSSHub 路径（如 /bilibili/user/video/316183842）
        timeout: 超时时间（秒）

    Returns:
        JSON 数据字典，失败返回 None
    """
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE

    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'application/json',
    }

    # 尝试多个实例
    for instance in RSSHUB_INSTANCES:
        url = f"{instance}{path}"
        try:
            request = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(request, timeout=timeout, context=ssl_context) as response:
                data = json.loads(response.read().decode('utf-8'))
                return data
        except Exception as e:
            print(f"RSSHub 实例 {instance} 请求失败: {e}")
            continue

    return None


async def fetch_bilibili_via_rsshub(mid: str, limit: int = 5) -> list[dict[str, Any]]:
    """
    通过 RSSHub 抓取 B站 UP主的最新视频

    Args:
        mid: UP主的用户ID
        limit: 获取视频数量

    Returns:
        视频列表，每个视频包含 title, url, published_at, summary
    """
    # RSSHub B站用户投稿路径
    path = f"/bilibili/user/video/{mid}"

    data = _fetch_rsshub_json(path)
    if not data:
        print(f"RSSHub 无法获取 B站 UP主 {mid} 的视频")
        return []

    items = data.get('items', [])
    if not items:
        print(f"B站 UP主 {mid} 没有找到视频")
        return []

    result = []
    for item in items[:limit]:
        # 解析发布时间
        published_at = ''
        if item.get('date_published'):
            try:
                dt = datetime.fromisoformat(item['date_published'].replace('Z', '+00:00'))
                published_at = dt.strftime('%Y-%m-%d %H:%M')
            except:
                pass

        result.append({
            "title": item.get('title', 'Unknown'),
            "url": item.get('url', ''),
            "published_at": published_at,
            "summary": item.get('summary', f"B站视频：{item.get('title', 'Unknown')[:50]}")
        })

    return result


async def fetch_youtube_via_rsshub(channel_id: str, limit: int = 5) -> list[dict[str, Any]]:
    """
    通过 RSSHub 抓取 YouTube 频道的最新视频

    Args:
        channel_id: 频道 ID（如 UCxxxxxxxxxx）或用户名（如 @dlcorner）
        limit: 获取视频数量

    Returns:
        视频列表，每个视频包含 title, url, published_at, summary
    """
    # 判断是频道 ID 还是用户名
    if channel_id.startswith('@'):
        # 用户名格式
        path = f"/youtube/user/{channel_id[1:]}"
    elif channel_id.startswith('UC'):
        # 频道 ID 格式
        path = f"/youtube/channel/{channel_id}"
    else:
        # 默认当作用户名
        path = f"/youtube/user/{channel_id}"

    data = _fetch_rsshub_json(path)
    if not data:
        print(f"RSSHub 无法获取 YouTube {channel_id} 的视频")
        return []

    items = data.get('items', [])
    if not items:
        print(f"YouTube {channel_id} 没有找到视频")
        return []

    result = []
    for item in items[:limit]:
        # 解析发布时间
        published_at = ''
        if item.get('date_published'):
            try:
                dt = datetime.fromisoformat(item['date_published'].replace('Z', '+00:00'))
                published_at = dt.strftime('%Y-%m-%d %H:%M')
            except:
                pass

        result.append({
            "title": item.get('title', 'Unknown'),
            "url": item.get('url', ''),
            "published_at": published_at,
            "summary": item.get('summary', f"YouTube视频：{item.get('title', 'Unknown')[:50]}")
        })

    return result


async def fetch_blog_via_rsshub(source: str, source_id: str, limit: int = 5) -> list[dict[str, Any]]:
    """
    通过 RSSHub 抓取博客内容

    Args:
        source: 来源类型（如 'anthropic', 'jesse'）
        source_id: RSSHub 路径标识
        limit: 获取文章数量

    Returns:
        文章列表，每篇包含 title, url, published_at, summary
    """
    # 预定义的博客路径映射
    blog_paths = {
        'anthropic': '/anthropic/blog',
        'jesse': '/ Jesse_vincent/blog',  # 如果有的话
    }

    path = blog_paths.get(source, source_id)
    if not path.startswith('/'):
        path = f"/{path}"

    data = _fetch_rsshub_json(path)
    if not data:
        print(f"RSSHub 无法获取博客 {source} 的内容")
        return []

    items = data.get('items', [])
    if not items:
        print(f"博客 {source} 没有找到文章")
        return []

    result = []
    for item in items[:limit]:
        # 解析发布时间
        published_at = ''
        if item.get('date_published'):
            try:
                dt = datetime.fromisoformat(item['date_published'].replace('Z', '+00:00'))
                published_at = dt.strftime('%Y-%m-%d')
            except:
                pass

        result.append({
            "title": item.get('title', 'Unknown'),
            "url": item.get('url', ''),
            "published_at": published_at,
            "summary": item.get('summary', '')[:200] if item.get('summary') else ''
        })

    return result
