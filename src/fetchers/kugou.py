"""酷狗音乐说唱先锋榜抓取器。

酷狗官方提供移动端 H5 榜单接口，无需登录即可访问：
- 榜单列表: https://m.kugou.com/rank/list?json=true
- 榜单详情: https://m.kugou.com/rank/info/{rank_id}?json=true

通过榜单列表可搜索到说唱先锋榜的 rank_id，当前为 265。
若接口结构变化，可在 config.yaml 中覆盖 api_url。
"""
import logging
from typing import Any, Dict, List

import requests

from src.utils import get_headers

logger = logging.getLogger("rap_report")

KUGOU_RANK_LIST_URL = "https://m.kugou.com/rank/list?json=true"
KUGOU_RANK_INFO_URL = "https://m.kugou.com/rank/info/{rank_id}?json=true"


class KugouFetcher:
    """酷狗榜单抓取器。"""

    def __init__(self) -> None:
        self.session = requests.Session()
        self.session.headers.update(get_headers())
        self.session.headers.update({
            "Referer": "https://m.kugou.com/",
            "Origin": "https://m.kugou.com",
        })

    def _find_rank_info(self, keyword: str = "说唱") -> Dict[str, Any]:
        """从酷狗榜单列表中搜索包含关键字的榜单完整信息。"""
        try:
            resp = self.session.get(KUGOU_RANK_LIST_URL, timeout=15)
            resp.raise_for_status()
            data = resp.json()
            ranks = data.get("rank", {}).get("list", [])
            for r in ranks:
                name = r.get("rankname", "")
                if keyword in name:
                    return {
                        "id": str(r.get("id", "")),
                        "rankid": str(r.get("rankid", "")),
                        "rank_cid": str(r.get("rank_cid", "")),
                    }
        except Exception as e:
            logger.warning("搜索酷狗榜单信息失败: %s", e)
        return {}

    def fetch_chart(self, list_id: str, name: str, api_url: str = "") -> Dict[str, Any]:
        """抓取酷狗榜单。

        如果 list_id 为空或占位值，会自动搜索说唱先锋榜 ID。
        """
        result: Dict[str, Any] = {
            "platform": "kugou",
            "chart_name": name,
            "list_id": list_id,
            "tracks": [],
            "total": 0,
            "success": False,
            "error": None,
        }

        rank_info: Dict[str, Any] = {}
        if not list_id or list_id in ("", "6666", "placeholder"):
            rank_info = self._find_rank_info("说唱")
            list_id = rank_info.get("id", "")
            if not list_id:
                result["error"] = (
                    "酷狗说唱先锋榜需要真实榜单 ID。"
                    "可通过 https://m.kugou.com/rank/list?json=true 搜索，"
                    "或更新 config.yaml 中的 platforms.kugou.list_id。"
                )
                logger.warning("酷狗《%s》无法确定榜单 ID", name)
                return result
            result["list_id"] = list_id
            logger.info("自动发现酷狗榜单 ID: %s", list_id)

        try:
            url = api_url or KUGOU_RANK_INFO_URL.format(rank_id=list_id)
            params: Dict[str, str] = {}
            if rank_info.get("rankid"):
                params["rankid"] = rank_info["rankid"]
            if rank_info.get("rank_cid"):
                params["rank_cid"] = rank_info["rank_cid"]
            resp = self.session.get(url, params=params, timeout=15)
            resp.raise_for_status()
            data = resp.json()
            tracks = self._parse_tracks(data)
            result["tracks"] = tracks
            result["total"] = len(tracks)
            result["success"] = True
            logger.info("酷狗《%s》抓取完成，共 %d 首", name, len(tracks))
        except requests.exceptions.RequestException as e:
            result["error"] = f"网络请求失败: {e}"
            logger.error("酷狗《%s》请求失败: %s", name, e)
        except Exception as e:
            result["error"] = f"解析失败: {e}"
            logger.error("酷狗《%s》解析失败: %s", name, e)

        return result

    def _parse_tracks(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """解析酷狗 API 返回的歌曲列表。

        H5 榜单详情结构: songs.list -> [{"songname": ..., "authors": [...], ...}]
        """
        tracks: List[Dict[str, Any]] = []
        songs: List[Dict[str, Any]] = []

        if isinstance(data, dict):
            songs = data.get("songs", {}).get("list", [])

        for idx, track in enumerate(songs, start=1):
            song_name = track.get("songname") or track.get("song_name") or track.get("name", "未知歌曲")
            authors = track.get("authors", [])
            if authors and isinstance(authors, list):
                artist = "/".join([a.get("author_name", "未知艺人") for a in authors])
            else:
                artist = track.get("singername") or track.get("singer_name") or track.get("singer", "未知艺人")
            album = track.get("album_name") or track.get("album", "未知专辑")
            tracks.append({
                "rank": track.get("sort", idx),
                "song_name": song_name,
                "artist": artist,
                "album": album,
                "is_new": False,
            })
        return tracks


def fetch_kugou(config: Dict[str, Any]) -> Dict[str, Any]:
    """抓取酷狗说唱先锋榜。"""
    cfg = config.get("platforms", {}).get("kugou", {})
    fetcher = KugouFetcher()
    return fetcher.fetch_chart(
        cfg.get("list_id", ""),
        cfg.get("name", "酷狗说唱先锋榜"),
        cfg.get("api_url", ""),
    )
