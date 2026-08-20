"""抓取器统一入口。"""
import logging
from typing import Any, Dict, List

from src.fetchers.hot_search import fetch_hot_search
from src.fetchers.kugou import fetch_kugou
from src.fetchers.netease import fetch_netease_chinese, fetch_netease_global
from src.fetchers.qq_music import fetch_qq_music

logger = logging.getLogger("rap_report")


def fetch_all(config: Dict[str, Any]) -> List[Dict[str, Any]]:
    """按配置抓取所有平台榜单。

    单个平台失败不影响其他平台继续抓取。
    """
    fetchers = [
        fetch_netease_chinese,
        fetch_netease_global,
        fetch_kugou,
        fetch_qq_music,
    ]
    results: List[Dict[str, Any]] = []
    for fetcher in fetchers:
        try:
            results.append(fetcher(config))
        except Exception as e:  # pragma: no cover - 保护主流程不因单个抓取器中断
            logger.error("抓取器 %s 异常: %s", fetcher.__name__, e)
            results.append({
                "platform": fetcher.__name__.replace("fetch_", ""),
                "chart_name": "未知榜单",
                "tracks": [],
                "total": 0,
                "success": False,
                "error": str(e),
            })
    return results


def fetch_all_hot_search(config: Dict[str, Any]) -> List[Dict[str, Any]]:
    """抓取微博/抖音热搜。"""
    return fetch_hot_search(config)
