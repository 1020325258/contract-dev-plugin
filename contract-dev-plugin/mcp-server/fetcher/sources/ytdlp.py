"""
视频抓取模块 - 使用 yt-dlp 命令行工具
yt-dlp 是一个成熟稳定的视频元数据提取工具，支持 YouTube 和 B站
"""

import asyncio
import json
import shutil
from typing import Any


def check_ytdlp_installed() -> bool:
    """检查 yt-dlp 是否已安装"""
    return shutil.which("yt-dlp") is not None or shutil.which("python3") is not None


async def run_ytdlp(url: str, limit: int = 5, timeout: int = 90) -> list[dict[str, Any]]:
    """
    使用 yt-dlp 获取视频列表

    Args:
        url: 视频列表页面 URL
        limit: 获取视频数量
        timeout: 超时时间（秒）

    Returns:
        视频列表，每个视频包含 title, url, published_at, summary
    """
    # 检查 yt-dlp 是否可用（优先使用 python3 -m yt_dlp）
    cmd_prefix = ["python3", "-m", "yt_dlp"]
    if not shutil.which("python3"):
        cmd_prefix = ["yt-dlp"]
        if not shutil.which("yt-dlp"):
            raise RuntimeError(
                "yt-dlp 未安装。请运行: pip3 install yt-dlp\n"
                "或访问: https://github.com/yt-dlp/yt-dlp#installation"
            )

    # yt-dlp 命令参数
    # --flat-playlist: 不下载视频，只获取元数据
    # --print: 输出格式
    # --no-warnings: 不显示警告
    cmd = cmd_prefix + [
        "--flat-playlist",
        "--print", "%(title)s|||%(url)s|||%(upload_date)s|||%(channel)s",
        "--no-warnings",
        "--playlist-end", str(limit),
        url
    ]

    try:
        # 运行命令
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        stdout, stderr = await asyncio.wait_for(
            process.communicate(),
            timeout=timeout
        )

        if process.returncode != 0:
            error_msg = stderr.decode('utf-8', errors='ignore').strip()
            raise RuntimeError(f"yt-dlp 执行失败: {error_msg}")

        # 解析输出
        output = stdout.decode('utf-8', errors='ignore')
        lines = [line.strip() for line in output.split('\n') if line.strip()]

        results = []
        for line in lines[:limit]:
            parts = line.split('|||')
            if len(parts) >= 3:
                title = parts[0].strip()
                video_url = parts[1].strip()
                upload_date = parts[2].strip() if len(parts) > 2 else ""
                channel = parts[3].strip() if len(parts) > 3 else ""

                # 格式化日期 (YYYYMMDD -> YYYY-MM-DD)
                published_at = ""
                if upload_date and len(upload_date) == 8 and upload_date.isdigit():
                    published_at = f"{upload_date[:4]}-{upload_date[4:6]}-{upload_date[6:8]}"

                results.append({
                    "title": title,
                    "url": video_url,
                    "published_at": published_at,
                    "summary": f"视频：{title[:50]}{'...' if len(title) > 50 else ''}"
                })

        return results

    except asyncio.TimeoutError:
        raise RuntimeError(f"yt-dlp 执行超时 ({timeout}秒)")


async def fetch_youtube_videos_ytdlp(channel: str, limit: int = 5) -> list[dict[str, Any]]:
    """
    使用 yt-dlp 抓取 YouTube 频道的最新视频

    Args:
        channel: 频道 handle (如 @dlcorner) 或频道 ID
        limit: 获取视频数量

    Returns:
        视频列表
    """
    # 构建 URL
    if channel.startswith("@"):
        url = f"https://www.youtube.com/{channel}/videos"
    elif channel.startswith("UC"):
        url = f"https://www.youtube.com/channel/{channel}/videos"
    else:
        url = f"https://www.youtube.com/@{channel}/videos"

    try:
        return await run_ytdlp(url, limit, timeout=90)
    except RuntimeError as e:
        error_str = str(e)
        if "timed out" in error_str.lower() or "timeout" in error_str.lower():
            raise RuntimeError(
                f"YouTube 连接超时，可能是网络问题。请检查:\n"
                f"1. 网络是否能访问 YouTube\n"
                f"2. 是否需要配置代理 (设置 HTTPS_PROXY 环境变量)\n"
                f"频道链接: {url}"
            )
        raise


async def fetch_bilibili_videos_ytdlp(mid: str, limit: int = 5) -> list[dict[str, Any]]:
    """
    使用 yt-dlp 抓取 B站 UP主的最新视频

    Args:
        mid: UP主的用户ID
        limit: 获取视频数量

    Returns:
        视频列表
    """
    url = f"https://space.bilibili.com/{mid}"

    # 先尝试直接抓取
    try:
        return await run_ytdlp(url, limit, timeout=30)
    except RuntimeError as e:
        error_str = str(e)
        # B站反爬或其他错误，尝试 RSSHub
        if "352" in error_str or "rejected" in error_str.lower():
            # 尝试使用 RSSHub 作为备选
            try:
                from .rsshub import fetch_bilibili_via_rsshub
                rsshub_result = await fetch_bilibili_via_rsshub(mid, limit)
                if rsshub_result:
                    return rsshub_result
            except Exception:
                pass

            raise RuntimeError(
                f"B站 UP主 {mid} 视频获取失败。原因: 反爬限制 (错误 352)\n"
                f"建议手动访问: https://space.bilibili.com/{mid}"
            )
        raise
