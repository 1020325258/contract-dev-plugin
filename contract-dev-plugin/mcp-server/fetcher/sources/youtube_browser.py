"""
YouTube视频抓取模块 - 使用 Playwright 浏览器
优化版本：解决超时问题，提高成功率
"""

import json
from typing import Any

from ..browser import BrowserManager


async def fetch_youtube_videos_browser(browser: BrowserManager, channel: str, limit: int = 5) -> list[dict[str, Any]]:
    """
    使用浏览器抓取 YouTube 频道的最新视频

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
        # 设置更长的默认超时
        page.set_default_timeout(60000)  # 60秒

        try:
            # 使用 domcontentloaded 而不是 networkidle，避免无限等待
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
        except Exception as e:
            # 如果超时，继续尝试提取内容
            print(f"页面加载警告: {e}")

        # 等待视频列表容器出现
        try:
            await page.wait_for_selector(
                "ytd-rich-item-renderer, ytd-grid-video-renderer, ytd-video-renderer",
                timeout=10000
            )
        except Exception:
            # 尝试滚动页面加载更多内容
            await page.evaluate("window.scrollTo(0, 800)")
            await page.wait_for_timeout(2000)

        # 等待一下让内容渲染
        await page.wait_for_timeout(3000)

        # 提取视频信息 - 使用更可靠的方法
        videos = await page.evaluate("""
            () => {
                const results = [];
                const elements = document.querySelectorAll(
                    'ytd-rich-item-renderer, ytd-grid-video-renderer, ytd-video-renderer'
                );

                for (const el of elements) {
                    if (results.length >= 15) break;

                    // 获取视频链接
                    const linkEl = el.querySelector('a[href*="/watch?v="]');
                    if (!linkEl) continue;

                    const href = linkEl.href;
                    if (!href || href.includes('googleads')) continue;

                    // 获取标题 - 多种方式尝试
                    let title = '';
                    const titleEl = el.querySelector('#video-title, a#video-title, [title]');
                    if (titleEl) {
                        title = titleEl.getAttribute('title') ||
                                titleEl.textContent?.trim() || '';
                    }

                    // 如果没有获取到标题，尝试其他方式
                    if (!title) {
                        const metaEl = el.querySelector('h3, #video-title-link');
                        if (metaEl) {
                            title = metaEl.textContent?.trim() || '';
                        }
                    }

                    // 清理标题
                    title = title.replace(/\\s+/g, ' ').trim().substring(0, 200);

                    // 过滤无效标题
                    if (!title || title.length < 2) continue;

                    // 尝试获取发布时间
                    let dateText = '';
                    const timeEl = el.querySelector('span.inline-metadata-item, ytd-video-meta-block span');
                    if (timeEl) {
                        dateText = timeEl.textContent?.trim() || '';
                    }

                    results.push({
                        title: title,
                        url: href,
                        date: dateText
                    });
                }

                return results;
            }
        """)

        result = []
        for video in videos[:limit]:
            result.append({
                "title": video.get('title', 'Unknown'),
                "url": video.get('url', ''),
                "published_at": video.get('date', ''),
                "summary": f"YouTube视频：{video.get('title', 'Unknown')[:50]}"
            })

        return result

    return await browser.with_page(scrape)
