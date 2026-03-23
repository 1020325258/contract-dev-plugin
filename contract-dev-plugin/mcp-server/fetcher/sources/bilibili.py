"""
B站视频抓取模块 - 使用 Playwright 浏览器
"""

import json
from datetime import datetime
from typing import Any

from ..browser import BrowserManager


async def fetch_bilibili_videos(browser: BrowserManager, mid: str, limit: int = 5) -> list[dict[str, Any]]:
    """
    抓取 B站 UP主的最新视频

    Args:
        browser: 浏览器管理器
        mid: UP主的用户ID
        limit: 获取视频数量

    Returns:
        视频列表，每个视频包含 title, url, published_at, summary
    """

    async def scrape(page):
        # 先访问 B站首页，获取 cookies
        await page.goto("https://www.bilibili.com", wait_until="domcontentloaded", timeout=30000)
        await page.wait_for_timeout(2000)

        # 通过浏览器环境调用 API（带 cookies）
        api_url = f"https://api.bilibili.com/x/space/arc/search?mid={mid}&ps=30&tid=0&pn=1&keyword=&order=pubdate"

        response_text = await page.evaluate(f'''
            async () => {{
                try {{
                    const res = await fetch('{api_url}');
                    return await res.text();
                }} catch (e) {{
                    return JSON.stringify({{ error: e.toString() }});
                }}
            }}
        ''')

        try:
            data = json.loads(response_text)
        except json.JSONDecodeError:
            print(f"B站 API 响应解析失败")
            return []

        if data.get('code') != 0:
            print(f"B站 API 错误: {data.get('message')}")
            return []

        vlist = data.get('data', {}).get('list', {}).get('vlist', [])
        if not vlist:
            print(f"B站 UP主 {mid} 没有找到视频")
            return []

        result = []
        for video in vlist[:limit]:
            created = video.get('created', 0)
            if created:
                published_at = datetime.fromtimestamp(created).strftime('%Y-%m-%d %H:%M')
            else:
                published_at = ''

            bvid = video.get('bvid', '')
            if bvid:
                video_url = f"https://www.bilibili.com/video/{bvid}"
            else:
                aid = video.get('aid', '')
                video_url = f"https://www.bilibili.com/video/av{aid}"

            result.append({
                "title": video.get('title', 'Unknown'),
                "url": video_url,
                "published_at": published_at,
                "summary": f"B站视频：{video.get('title', 'Unknown')[:50]}"
            })

        return result

    return await browser.with_page(scrape)
