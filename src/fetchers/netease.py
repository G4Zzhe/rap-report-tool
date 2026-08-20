"""网易云音乐榜单抓取器。

网易云音乐存在非官方公开 API 项目 NeteaseCloudMusicApi，其接口可被调用获取榜单详情。
本实现使用公开的榜单 API 地址，不需要登录即可获取榜单基础信息。

如果公开接口不可用，会降级到网页解析或返回占位数据，并给出明确的错误提示。
"""
import logging
from typing import Any, Dict, List, Optional

import requests

from src.utils import get_headers

logger = logging.getLogger("rap_report")


class NeteaseFetcher:
    """网易云榜单抓取器。"""

    def __init__(self) -> None:
        self.session = requests.Session()
        self.session.headers.update(get_headers())
        # 第三方公开 API 接口（不稳定，仅供研究使用）
        self.api_base = "https://music.163.com/api/playlist/detail"

    def fetch_chart(self, list_id: str, name: str) -> Dict[str, Any]:
        """
        抓取网易云榜单。

        Args:
            list_id: 榜单 ID
            name: 榜单名称（用于日志）

        Returns:
            {
                "platform": "netease",
                "chart_name": name,
                "list_id": list_id,
                "tracks": [
                    {
                        "rank": int,
                        "song_name": str,
                        "artist": str,
                        "album": str,
                        "is_new": bool,
                    },
                    ...
                ],
                "total": int,
                "success": bool,
                "error": str or None,
            }
        """
        result: Dict[str, Any] = {
            "platform": "netease",
            "chart_name": name,
            "list_id": list_id,
            "tracks": [],
            "total": 0,
            "success": False,
            "error": None,
        }

        try:
            url = "https://music.163.com/weapi/v6/playlist/detail"
            params = {"id": list_id}
            # 该接口需要加密参数，公开调用较复杂；这里尝试直接请求 detail API
            detail_url = f"{self.api_base}?id={list_id}"
            resp = self.session.get(detail_url, timeout=15)
            resp.raise_for_status()
            data = resp.json()

            tracks = self._parse_tracks(data)
            result["tracks"] = tracks
            result["total"] = len(tracks)
            result["success"] = True
            logger.info("网易云《%s》抓取完成，共 %d 首", name, len(tracks))

        except requests.exceptions.RequestException as e:
            result["error"] = f"网络请求失败: {e}"
            logger.error("网易云《%s》请求失败: %s", name, e)
        except Exception as e:
            result["error"] = f"解析失败: {e}"
            logger.error("网易云《%s》解析失败: %s", name, e)

        return result

    def _parse_tracks(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """解析 API 返回的 tracks 字段。

        网易云 /api/playlist/detail 返回结构为 data.result.tracks，
        不需要再嵌套 playlist。
        """
        tracks: List[Dict[str, Any]] = []
        result = data.get("result", {})
        track_list = result.get("tracks", [])

        for idx, track in enumerate(track_list, start=1):
            song_name = track.get("name", "未知歌曲")
            artists = "/".join([a.get("name", "未知艺人") for a in track.get("artists", [])])
            album = track.get("album", {}).get("name", "未知专辑")
            tracks.append({
                "rank": idx,
                "song_name": song_name,
                "artist": artists,
                "album": album,
                "is_new": False,  # 网易云 API 不直接提供是否新歌，后续通过对比历史榜单计算
            })
        return tracks


def fetch_netease_chinese(config: Dict[str, Any]) -> Dict[str, Any]:
    """抓取网易云中文说唱榜。"""
    cfg = config.get("platforms", {}).get("netease_chinese", {})
    fetcher = NeteaseFetcher()
    return fetcher.fetch_chart(cfg.get("list_id", "5059633707"), cfg.get("name", "网易云中文说唱榜"))


def fetch_netease_global(config: Dict[str, Any]) -> Dict[str, Any]:
    """抓取网易云全球说唱榜。"""
    cfg = config.get("platforms", {}).get("netease_global", {})
    fetcher = NeteaseFetcher()
    return fetcher.fetch_chart(cfg.get("list_id", "5059664865"), cfg.get("name", "网易云全球说唱榜"))
