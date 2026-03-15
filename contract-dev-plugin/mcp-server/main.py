#!/usr/bin/env python3
"""
Content Fetcher MCP Server
使用 Playwright 抓取博客和视频网站的最新内容
"""

import asyncio
import json
import sys
from datetime import datetime
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from fetcher.browser import BrowserManager
from fetcher.sources import (
    fetch_anthropic_blog,
    fetch_jesse_blog,
    fetch_bilibili_videos,
    fetch_youtube_videos,
)

# 创建 MCP Server 实例
server = Server("content-fetcher")

# 浏览器管理器
browser_manager: BrowserManager | None = None


@server.list_tools()
async def list_tools() -> list[Tool]:
    """列出所有可用的 MCP 工具"""
    return [
        Tool(
            name="fetch_anthropic_blog",
            description="抓取 Anthropic Engineering 博客的最新文章",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "获取文章数量，默认 5",
                        "default": 5
                    }
                }
            }
        ),
        Tool(
            name="fetch_jesse_blog",
            description="抓取 Jesse Vincent 博客 (blog.fsck.com) 的最新文章",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "获取文章数量，默认 5",
                        "default": 5
                    }
                }
            }
        ),
        Tool(
            name="fetch_bilibili_videos",
            description="抓取 B站 UP主的最新视频",
            inputSchema={
                "type": "object",
                "properties": {
                    "mid": {
                        "type": "string",
                        "description": "UP主的 mid (用户ID)"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "获取视频数量，默认 5",
                        "default": 5
                    }
                },
                "required": ["mid"]
            }
        ),
        Tool(
            name="fetch_youtube_videos",
            description="抓取 YouTube 频道的最新视频",
            inputSchema={
                "type": "object",
                "properties": {
                    "channel": {
                        "type": "string",
                        "description": "频道 handle (如 @dlcorner) 或频道 ID"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "获取视频数量，默认 5",
                        "default": 5
                    }
                },
                "required": ["channel"]
            }
        ),
        Tool(
            name="fetch_all_content",
            description="一次性抓取所有配置的数据源",
            inputSchema={
                "type": "object",
                "properties": {
                    "sources": {
                        "type": "array",
                        "description": "数据源配置列表",
                        "items": {
                            "type": "object",
                            "properties": {
                                "type": {"type": "string"},
                                "name": {"type": "string"},
                                "url": {"type": "string"},
                                "mid": {"type": "string"},
                                "channel": {"type": "string"}
                            }
                        }
                    }
                },
                "required": ["sources"]
            }
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    """处理工具调用"""
    global browser_manager

    try:
        # 确保浏览器已启动
        if browser_manager is None:
            browser_manager = BrowserManager()
            await browser_manager.start()

        limit = arguments.get("limit", 5)
        result = None

        if name == "fetch_anthropic_blog":
            result = await fetch_anthropic_blog(browser_manager, limit)
        elif name == "fetch_jesse_blog":
            result = await fetch_jesse_blog(browser_manager, limit)
        elif name == "fetch_bilibili_videos":
            mid = arguments["mid"]
            result = await fetch_bilibili_videos(browser_manager, mid, limit)
        elif name == "fetch_youtube_videos":
            channel = arguments["channel"]
            result = await fetch_youtube_videos(browser_manager, channel, limit)
        elif name == "fetch_all_content":
            sources = arguments["sources"]
            result = await fetch_all_sources(browser_manager, sources)
        else:
            return [TextContent(type="text", text=f"未知工具: {name}")]

        return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))]

    except Exception as e:
        return [TextContent(type="text", text=f"错误: {str(e)}")]


async def fetch_all_sources(browser: BrowserManager, sources: list[dict]) -> dict:
    """抓取所有数据源"""
    results = {
        "blogs": [],
        "videos": [],
        "errors": [],
        "fetched_at": datetime.now().isoformat()
    }

    for source in sources:
        source_type = source.get("type")
        source_name = source.get("name", "Unknown")

        try:
            if source_type == "blog":
                if "anthropic" in source.get("url", ""):
                    articles = await fetch_anthropic_blog(browser, 5)
                    results["blogs"].extend(articles)
                elif "fsck" in source.get("url", ""):
                    articles = await fetch_jesse_blog(browser, 5)
                    results["blogs"].extend(articles)
            elif source_type == "bilibili":
                mid = source.get("space_id")
                if mid:
                    videos = await fetch_bilibili_videos(browser, mid, 5)
                    for v in videos:
                        v["source"] = source_name
                    results["videos"].extend(videos)
            elif source_type == "youtube":
                channel = source.get("channel")
                if channel:
                    videos = await fetch_youtube_videos(browser, channel, 5)
                    for v in videos:
                        v["source"] = source_name
                    results["videos"].extend(videos)
        except Exception as e:
            results["errors"].append({
                "source": source_name,
                "error": str(e)
            })

    return results


async def cleanup():
    """清理资源"""
    global browser_manager
    if browser_manager:
        await browser_manager.close()
        browser_manager = None


async def main():
    """主入口"""
    async with stdio_server() as (read_stream, write_stream):
        try:
            await server.run(
                read_stream,
                write_stream,
                server.create_initialization_options()
            )
        finally:
            await cleanup()


if __name__ == "__main__":
    asyncio.run(main())
