"""
博客抓取模块
"""

import re
from typing import Any

from ..browser import BrowserManager


async def fetch_anthropic_blog(browser: BrowserManager, limit: int = 5) -> list[dict[str, Any]]:
    """
    抓取 Anthropic Engineering 博客最新文章
    """
    url = "https://www.anthropic.com/engineering"

    async def scrape(page):
        await page.goto(url, wait_until="networkidle", timeout=30000)

        # 等待页面加载
        await page.wait_for_selector("a[href*='/engineering/']", timeout=15000)

        # 提取文章链接
        articles = await page.eval_on_selector_all(
            "a[href*='/engineering/']",
            """elements => {
                const seen = new Set();
                return elements.map(el => {
                    const href = el.href;
                    // 过滤非文章链接
                    if (href === 'https://www.anthropic.com/engineering' || seen.has(href)) {
                        return null;
                    }
                    seen.add(href);
                    return {
                        title: el.textContent?.trim() || '',
                        url: href
                    };
                }).filter(item => item && item.title && item.title.length > 5);
            }"""
        )

        # 清理和限制数量
        result = []
        for article in articles[:limit]:
            title = re.sub(r'\s+', ' ', article['title']).strip()
            title = re.sub(r'\s*\\?\s*Anthropic\s*$', '', title).strip()

            result.append({
                "title": title,
                "url": article['url'],
                "published_at": None,
                "summary": f"来自 Anthropic Engineering 的文章：{title}"
            })

        return result

    return await browser.with_page(scrape)


async def fetch_jesse_blog(browser: BrowserManager, limit: int = 5) -> list[dict[str, Any]]:
    """
    抓取 Jesse Vincent 博客 (blog.fsck.com) 最新文章
    """
    url = "https://blog.fsck.com/"

    async def scrape(page):
        await page.goto(url, wait_until="networkidle", timeout=30000)

        # 等待文章列表加载
        await page.wait_for_selector(".post-item, article", timeout=15000)

        # 提取文章信息
        articles = await page.eval_on_selector_all(
            ".post-item, article",
            """elements => {
                return elements.map(el => {
                    const titleEl = el.querySelector('.post-title a, h3 a, h2 a');
                    const dateEl = el.querySelector('.post-date, time');
                    return {
                        title: titleEl?.textContent?.trim() || '',
                        url: titleEl?.href || '',
                        date: dateEl?.textContent?.trim() || ''
                    };
                }).filter(item => item.title && item.url);
            }"""
        )

        result = []
        for article in articles[:limit]:
            result.append({
                "title": article['title'],
                "url": article['url'],
                "published_at": article['date'],
                "summary": f"来自 Jesse Vincent 博客的文章：{article['title']}"
            })

        return result

    return await browser.with_page(scrape)
