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
        await page.goto(url, wait_until="domcontentloaded", timeout=30000)

        # 等待页面加载
        await page.wait_for_timeout(3000)

        # 提取视频信息 - 使用更可靠的选择器
        videos = await page.eval_on_selector_all(
            "ytd-rich-item-renderer, ytd-grid-video-renderer, ytd-video-renderer",
            """elements => {
                const results = [];

                for (const el of elements) {
                    // 获取视频链接
                    const linkEl = el.querySelector('a[href*="/watch?v="]');
                    if (!linkEl) continue;

                    const href = linkEl.href;
                    if (!href) continue;

                    // 获取标题 - 优先从 title 属性获取
                    const titleEl = el.querySelector('#video-title, a#video-title, [title]');
                    let title = '';
                    if (titleEl) {
                        title = titleEl.getAttribute('title') ||
                                titleEl.textContent?.trim() || '';
                    }

                    // 清理标题
                    title = title.replace(/\\s+/g, ' ').trim().substring(0, 100);

                    // 过滤无效标题（如纯时长）
                    if (!title || /^\\d+:\\d+$/.test(title) || title.length < 2) {
                        continue;
                    }

                    results.push({
                        title: title,
                        url: href,
                        date: ''
                    });

                    if (results.length >= 10) break;
                }

                return results;
            }"""
        )

        result = []
        for video in videos[:limit]:
            result.append({
                "title": video['title'] or "Unknown",
                "url": video['url'],
                "published_at": video['date'],
                "summary": f"YouTube视频：{(video['title'] or 'Unknown')[:50]}"
            })

        return result

    return await browser.with_page(scrape)
