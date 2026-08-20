"""榜单数据聚合分析。

将各平台抓取结果统一转换为 DataFrame，并计算：
- 艺人跨平台上榜次数与最高排名
- 歌曲跨平台表现
- 各平台新歌数量（需要上一期历史数据）
- 排名上升/下降 TOP
- 连续霸榜歌曲（需要上一期历史数据）
"""
import logging
from collections import defaultdict
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

logger = logging.getLogger("rap_report")


def normalize_platform_name(platform: str) -> str:
    """统一平台名称。"""
    mapping = {
        "netease": "网易云音乐",
        "netease_chinese": "网易云中文说唱榜",
        "netease_global": "网易云全球说唱榜",
        "kugou": "酷狗音乐",
        "qq_music": "QQ音乐",
    }
    return mapping.get(platform, platform)


def chart_name_to_platform(chart_name: str) -> str:
    """根据榜单名称推断平台（用于分开展示多个网易云榜单）。"""
    if "全球" in chart_name:
        return "网易云全球说唱榜"
    if "中文" in chart_name or "说唱" in chart_name:
        return chart_name
    return "网易云音乐"


def flatten_results(results: List[Dict[str, Any]]) -> pd.DataFrame:
    """将各平台抓取结果合并成一个 DataFrame，平台名使用中文榜单名。"""
    rows = []
    for result in results:
        platform = normalize_platform_name(result.get("platform", "unknown"))
        chart_name = result.get("chart_name", "")
        # 网易云不同榜单用 chart_name 区分平台展示
        display_platform = chart_name if "网易云" in chart_name else platform
        tracks = result.get("tracks", [])
        for track in tracks:
            rows.append({
                "platform": display_platform,
                "chart_name": chart_name,
                "rank": track.get("rank"),
                "song_name": track.get("song_name", ""),
                "artist": track.get("artist", ""),
                "album": track.get("album", ""),
                "is_new": track.get("is_new", False),
            })
    return pd.DataFrame(rows)


def artist_summary(df: pd.DataFrame) -> pd.DataFrame:
    """统计艺人跨平台上榜情况。"""
    if df.empty:
        return pd.DataFrame()

    summary = []
    for artist, group in df.groupby("artist"):
        platforms = group["platform"].unique().tolist()
        total = len(group)
        best_rank = group["rank"].min()
        best_song = group.loc[group["rank"].idxmin(), "song_name"]
        summary.append({
            "artist": artist,
            "total_entries": total,
            "platforms": ",".join(platforms),
            "platform_count": len(platforms),
            "best_rank": int(best_rank),
            "best_song": best_song,
        })

    summary_df = pd.DataFrame(summary)
    if not summary_df.empty:
        summary_df = summary_df.sort_values(
            by=["total_entries", "platform_count", "best_rank"],
            ascending=[False, False, True],
        ).reset_index(drop=True)
    return summary_df


def song_summary(df: pd.DataFrame) -> pd.DataFrame:
    """统计歌曲跨平台表现。"""
    if df.empty:
        return pd.DataFrame()

    summary = []
    for key, group in df.groupby(["song_name", "artist"]):
        song_name, artist = key
        platforms = group["platform"].unique().tolist()
        best_rank = group["rank"].min()
        best_platform = group.loc[group["rank"].idxmin(), "platform"]
        summary.append({
            "song_name": song_name,
            "artist": artist,
            "platforms": ",".join(platforms),
            "platform_count": len(platforms),
            "best_rank": int(best_rank),
            "best_platform": best_platform,
        })

    summary_df = pd.DataFrame(summary)
    if not summary_df.empty:
        summary_df = summary_df.sort_values(
            by=["platform_count", "best_rank"],
            ascending=[False, True],
        ).reset_index(drop=True)
    return summary_df


def new_songs_count(df: pd.DataFrame, history_df: Optional[pd.DataFrame] = None) -> Dict[str, int]:
    """计算各平台新歌数量。

    当前简单规则：如果歌曲未在历史榜单中出现，则认为是新歌。
    如果没有历史数据，返回空字典。
    """
    if history_df is None or history_df.empty or df.empty:
        return {}

    history_songs = set(zip(history_df["song_name"], history_df["artist"]))
    new_counts = {}
    for platform, group in df.groupby("platform"):
        current_songs = set(zip(group["song_name"], group["artist"]))
        new_songs = current_songs - history_songs
        new_counts[platform] = len(new_songs)
    return new_counts


def rank_changes(df: pd.DataFrame, history_df: Optional[pd.DataFrame] = None) -> pd.DataFrame:
    """计算歌曲排名变化。

    返回包含 rank_change（上升为正，下降为负）的 DataFrame。
    """
    if history_df is None or history_df.empty or df.empty:
        return pd.DataFrame()

    history = history_df.set_index(["song_name", "artist", "platform"])["rank"].to_dict()
    changes = []
    for _, row in df.iterrows():
        key = (row["song_name"], row["artist"], row["platform"])
        prev_rank = history.get(key)
        if prev_rank is not None:
            change = prev_rank - row["rank"]
            changes.append({
                "platform": row["platform"],
                "chart_name": row["chart_name"],
                "song_name": row["song_name"],
                "artist": row["artist"],
                "current_rank": row["rank"],
                "previous_rank": prev_rank,
                "rank_change": change,
            })

    changes_df = pd.DataFrame(changes)
    if not changes_df.empty:
        changes_df = changes_df.sort_values(by="rank_change", ascending=False).reset_index(drop=True)
    return changes_df


def cross_platform_hits(df: pd.DataFrame, min_platforms: int = 2) -> pd.DataFrame:
    """找出跨平台爆款（在至少 min_platforms 个平台同时上榜的歌曲）。"""
    song_df = song_summary(df)
    if song_df.empty:
        return song_df
    return song_df[song_df["platform_count"] >= min_platforms].reset_index(drop=True)


def analyze(results: List[Dict[str, Any]], history_results: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
    """执行完整聚合分析。"""
    df = flatten_results(results)
    history_df = flatten_results(history_results) if history_results else None

    analysis = {
        "raw": df,
        "artist_summary": artist_summary(df),
        "song_summary": song_summary(df),
        "cross_platform_hits": cross_platform_hits(df),
        "new_songs_count": new_songs_count(df, history_df),
        "rank_changes": rank_changes(df, history_df),
        "total_songs": len(df),
        "total_platforms": df["platform"].nunique() if not df.empty else 0,
    }
    logger.info("聚合分析完成：%d 首歌，%d 个平台", analysis["total_songs"], analysis["total_platforms"])
    return analysis
