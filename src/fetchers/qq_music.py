"""QQ 音乐说唱榜抓取器。

QQ 音乐榜单通过公开接口 `musicu.fcg` 获取，本实现使用官方榜单接口：
- 接口: https://u.y.qq.com/cgi-bin/musicu.fcg
- 方法: musicToplist.ToplistInfoServer.GetDetail
- 说唱榜 topId: 58

无需登录即可获取完整榜单，但榜单 ID 可能随业务调整而变化，可在
config.yaml 中覆盖。
"""
import json
import logging
import urllib.parse
from typing import Any, Dict, List

import requests

from src.utils import get_headers

logger = logging.getLogger("rap_report")

QQ_TOP_DETAIL_URL = "https://u.y.qq.com/cgi-bin/musicu.fcg"


class QQMusicFetcher:
    """QQ 音乐榜单抓取器。"""

    def __init__(self) -> None:
        self.session = requests.Session()
        self.session.headers.update(get_headers())
        self.session.headers.update({
            "Referer": "https://y.qq.com/",
            "Origin": "https://y.qq.com",
        })

    def fetch_chart(self, list_id: str, name: str, api_url: str = "") -> Dict[str, Any]:
        """抓取 QQ 音乐榜单。"""
        result: Dict[str, Any] = {
            "platform": "qq_music",
            "chart_name": name,
            "list_id": list_id,
            "tracks": [],
            "total": 0,
            "success": False,
            "error": None,
        }

        if not list_id or list_id in ("", "62", "placeholder"):
            result["error"] = (
                "QQ 音乐说唱榜需要配置真实榜单 ID。"
                "默认使用官方说唱榜 topId=58，可在 config.yaml 中覆盖。"
            )
            logger.warning("QQ 音乐《%s》缺少榜单 ID", name)
            return result

        try:
            payload = {
                "req_0": {
                    "module": "musicToplist.ToplistInfoServer",
                    "method": "GetDetail",
                    "param": {
                        "topId": int(list_id),
                        "offset": 0,
                        "num": 100,
                        "period": "",
                    },
                }
            }
            url = api_url or f"{QQ_TOP_DETAIL_URL}?data={urllib.parse.quote(json.dumps(payload))}"
            resp = self.session.get(url, timeout=15)
            resp.raise_for_status()
            data = resp.json()
            tracks = self._parse_tracks(data)
            result["tracks"] = tracks
            result["total"] = len(tracks)
            result["success"] = True
            logger.info("QQ 音乐《%s》抓取完成，共 %d 首", name, len(tracks))
        except requests.exceptions.RequestException as e:
            result["error"] = f"网络请求失败: {e}"
            logger.error("QQ 音乐《%s》请求失败: %s", name, e)
        except Exception as e:
            result["error"] = f"解析失败: {e}"
            logger.error("QQ 音乐《%s》解析失败: %s", name, e)

        return result

    def _parse_tracks(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """解析 QQ 音乐 GetDetail 返回的歌曲列表。

        返回结构: req_0.data.data.song
        """
        tracks: List[Dict[str, Any]] = []
        songs: List[Dict[str, Any]] = []

        if isinstance(data, dict):
            detail = data.get("req_0", {}).get("data", {}).get("data", {})
            songs = detail.get("song", [])

        for idx, track in enumerate(songs, start=1):
            song_name = track.get("title") or track.get("name", "未知歌曲")
            artist = track.get("singerName", "未知艺人")
            album = track.get("albumname") or track.get("album", "未知专辑")
            tracks.append({
                "rank": track.get("rank", idx),
                "song_name": song_name,
                "artist": artist,
                "album": album,
                "is_new": False,
            })
        return tracks


def fetch_qq_music(config: Dict[str, Any]) -> Dict[str, Any]:
    """抓取 QQ 音乐说唱榜。"""
    cfg = config.get("platforms", {}).get("qq_music", {})
    fetcher = QQMusicFetcher()
    return fetcher.fetch_chart(
        cfg.get("list_id", "58"),
        cfg.get("name", "QQ音乐说唱榜"),
        cfg.get("api_url", ""),
    )
