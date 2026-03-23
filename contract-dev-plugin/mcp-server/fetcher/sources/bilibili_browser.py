"""
B站视频抓取模块 - 使用 Playwright 浏览器
直接访问用户空间页面抓取视频列表
"""

import json
from datetime import datetime
from typing import Any

from ..browser import BrowserManager


async def fetch_bilibili_videos_browser(browser: BrowserManager, mid: str, limit: int = 5) -> list[dict[str, Any]]:
    """
    使用浏览器抓取 B站 UP主的最新视频

    策略：直接访问用户空间页面，等待内容加载后提取

    Args:
        browser: 浏览器管理器
        mid: UP主的用户ID
        limit: 获取视频数量

    Returns:
        视频列表，每个视频包含 title, url, published_at, summary
    """

    async def scrape(page):
        page.set_default_timeout(60000)

        # 访问用户空间视频页面
        url = f"https://space.bilibili.com/{mid}/upload/video"
        print(f"访问: {url}")

        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
        except Exception as e:
            print(f"页面加载警告: {e}")

        # 等待页面内容加载
        await page.wait_for_timeout(5000)

        # 检查是否需要登录
        login_required = await page.evaluate('''
            () => {
                // 检查是否有登录提示
                const loginModal = document.querySelector('.login-panel, .login-scan-wp, [class*="login"]');
                return loginModal !== null;
            }
        ''')

        if login_required:
            print("检测到登录要求，尝试继续...")

        # 尝试滚动加载更多内容
        await page.evaluate('window.scrollTo(0, 1000)')
        await page.wait_for_timeout(2000)
        await page.evaluate('window.scrollTo(0, 2000)')
        await page.wait_for_timeout(2000)

        # 提取视频信息
        videos = await page.evaluate(f'''
            () => {{
                const results = [];
                const seen = new Set();

                // 尝试多种选择器
                const selectors = [
                    '.small-item .item',
                    '.bili-video-card',
                    '.video-list .list-item',
                    '.cube-list-item',
                    '[data-mod="space_video"] .small-item',
                    '.video-item'
                ];

                for (const selector of selectors) {{
                    const items = document.querySelectorAll(selector);
                    console.log('Selector:', selector, 'Found:', items.length);

                    for (const item of items) {{
                        if (results.length >= {limit * 2}) break;

                        // 获取链接
                        const linkEl = item.querySelector('a[href*="/video/"]');
                        if (!linkEl) continue;

                        const href = linkEl.href;
                        if (seen.has(href)) continue;
                        seen.add(href);

                        // 获取标题
                        const titleEl = item.querySelector('[title], .title, a[title], .bili-video-card__info--tit, h3');
                        let title = '';
                        if (titleEl) {{
                            title = titleEl.getAttribute('title') || titleEl.textContent?.trim() || '';
                        }}
                        if (!title) {{
                            title = linkEl.getAttribute('title') || linkEl.textContent?.trim() || 'Unknown';
                        }}

                        // 清理标题
                        title = title.replace(/\\s+/g, ' ').trim().substring(0, 100);

                        // 获取播放量和发布时间
                        let dateText = '';
                        const stats = item.querySelectorAll('.bili-video-card__info--bottom span, .stats .item, .meta span');
                        for (const stat of stats) {{
                            const text = stat.textContent?.trim() || '';
                            if (text.includes('发布') || text.includes('前') || text.includes('天')) {{
                                dateText = text;
                                break;
                            }}
                        }}

                        results.push({{
                            title: title,
                            url: href,
                            date: dateText
                        }});
                    }}

                    if (results.length >= {limit * 2}) break;
                }}

                return results;
            }}
        ''')

        print(f"提取到 {len(videos)} 个视频")

        result = []
        for video in videos[:limit]:
            title = video.get('title', 'Unknown')
            if not title or title == 'Unknown':
                continue

            result.append({
                "title": title,
                "url": video.get('url', ''),
                "published_at": video.get('date', ''),
                "summary": f"B站视频：{title[:50]}"
            })

        return result

    return await browser.with_page(scrape)
