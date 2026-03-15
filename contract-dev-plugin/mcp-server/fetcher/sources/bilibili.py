"""
B站视频抓取模块
"""

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
    url = f"https://space.bilibili.com/{mid}"

    async def scrape(page):
        await page.goto(url, wait_until="networkidle", timeout=30000)

        # 等待视频列表加载
        await page.wait_for_selector(".small-item, .list-item", timeout=15000)

        # 提取视频信息
        videos = await page.eval_on_selector_all(
            ".small-item, .list-item",
            """elements => {
                return elements.map(el => {
                    const titleEl = el.querySelector('.title, a[title]');
                    const linkEl = el.querySelector('a[href*="/video/"]');
                    const dateEl = el.querySelector('.time, .date');

                    return {
                        title: titleEl?.getAttribute('title') || titleEl?.textContent?.trim() || '',
                        url: linkEl?.href || '',
                        date: dateEl?.textContent?.trim() || ''
                    };
                }).filter(item => item.title && item.url);
            }"""
        )

        result = []
        for video in videos[:limit]:
            result.append({
                "title": video['title'],
                "url": video['url'],
                "published_at": video['date'],
                "summary": f"B站视频：{video['title']}"
            })

        return result

    return await browser.with_page(scrape)
