"""
YouTube视频抓取模块
"""

from typing import Any

from ..browser import BrowserManager


async def fetch_youtube_videos(browser: BrowserManager, channel: str, limit: int = 5) -> list[dict[str, Any]]:
    """
    抓取 YouTube 频道的最新视频

    Args:
        browser: 浏览器管理器
        channel: 频道 handle (如 @dlcorner) 或频道 ID
        limit: 获取视频数量

    Returns:
        视频列表，每个视频包含 title, url, published_at, summary
    """
    # 构建 URL
    if channel.startswith("@"):
        url = f"https://www.youtube.com/{channel}/videos"
    elif channel.startswith("UC"):
        url = f"https://www.youtube.com/channel/{channel}/videos"
    else:
        url = f"https://www.youtube.com/@{channel}/videos"

    async def scrape(page):
        await page.goto(url, wait_until="networkidle", timeout=30000)

        # 等待视频列表加载
        await page.wait_for_selector("a[href*='/watch?v='], ytd-rich-item-renderer", timeout=15000)

        # 提取视频信息
        videos = await page.eval_on_selector_all(
            "ytd-rich-item-renderer, ytd-grid-video-renderer",
            """elements => {
                const seen = new Set();
                return elements.map(el => {
                    const titleEl = el.querySelector('#video-title, a[title]');
                    const linkEl = el.querySelector('a[href*="/watch"]');
                    const metaEl = el.querySelector('ytd-video-meta-block, .metadata');

                    const title = titleEl?.getAttribute('title') || titleEl?.textContent?.trim() || '';
                    const url = linkEl?.href || '';

                    // 提取发布时间
                    let date = '';
                    const metaText = metaEl?.textContent || '';
                    const viewsMatch = metaText.match(/(\\d+\\.?\\d*[KMB]?\\s*views|\\d+\\.?\\d*[KMB]?\\s*次观看)/i);
                    const timeMatch = metaText.match(/(\\d+\\s*(hour|day|week|month|year)s?\\s*ago|\\d+\\s*(小时|天|周|月|年)前)/i);

                    if (timeMatch) {
                        date = timeMatch[0];
                    }

                    // 过滤重复
                    if (seen.has(url) || !title || !url) {
                        return null;
                    }
                    seen.add(url);

                    return { title, url, date };
                }).filter(item => item);
            }"""
        )

        result = []
        for video in videos[:limit]:
            result.append({
                "title": video['title'],
                "url": video['url'],
                "published_at": video['date'],
                "summary": f"YouTube视频：{video['title']}"
            })

        return result

    return await browser.with_page(scrape)
