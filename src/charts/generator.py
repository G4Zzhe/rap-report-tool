"""图表生成模块。

使用 matplotlib 生成报告中需要的静态图表：
- 头部艺人上榜曲目数柱状图
- 各平台新歌数量柱状图
- 跨平台爆款歌曲数量对比
- 平台歌曲分布饼图
- 艺人跨平台覆盖雷达图
- 歌曲上榜平台数矩形树图
- 排名变化趋势图（需历史数据）
"""
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

import matplotlib
import matplotlib.font_manager as fm
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import squarify

from src.utils import OUTPUT_DIR

logger = logging.getLogger("rap_report")

matplotlib.use("Agg")

# 配置中文字体：优先使用 Windows 常见字体，回退到 Linux 字体
_CHINESE_FONT_NAMES = [
    "Microsoft YaHei",
    "SimHei",
    "Noto Sans SC",
    "Noto Serif SC",
    "WenQuanYi Micro Hei",
]


def _find_chinese_font() -> fm.FontProperties:
    """查找系统中可用的中文字体并返回 FontProperties。"""
    for name in _CHINESE_FONT_NAMES:
        try:
            path = fm.findfont(name, fallback_to_default=False)
            if path and "DejaVu" not in path:
                return fm.FontProperties(fname=path)
        except Exception:
            continue
    return fm.FontProperties()


# 全局中文字体属性
_CHINESE_FONT_PROP = _find_chinese_font()
plt.rcParams["axes.unicode_minus"] = False
logger.info("图表使用中文字体: %s", _CHINESE_FONT_PROP.get_name())


def _apply_font(ax: plt.Axes, fontprop: fm.FontProperties, labels: bool = True) -> None:
    """将中文字体应用到图表标题、坐标轴标签和刻度文字。"""
    if ax.title.get_text():
        ax.title.set_fontproperties(fontprop)
    ax.set_xlabel(ax.get_xlabel(), fontproperties=fontprop)
    ax.set_ylabel(ax.get_ylabel(), fontproperties=fontprop)
    if labels:
        for label in ax.get_xticklabels() + ax.get_yticklabels():
            label.set_fontproperties(fontprop)


class ChartGenerator:
    """图表生成器。"""

    def __init__(self, config: Dict[str, Any]) -> None:
        self.config = config.get("charts", {})
        self.brand_color = self.config.get("brand_color", "#1f4e99")
        self.secondary_color = self.config.get("secondary_color", "#f5a623")
        self.negative_color = self.config.get("negative_color", "#e94b3c")
        self.style = self.config.get("style", "seaborn-v0_8-whitegrid")
        try:
            plt.style.use(self.style)
        except OSError:
            plt.style.use("default")

    def save(self, fig: plt.Figure, filename: str) -> Path:
        """保存图表到 output 目录。"""
        path = OUTPUT_DIR / filename
        fig.savefig(path, dpi=150, bbox_inches="tight", facecolor="white")
        plt.close(fig)
        logger.info("图表已保存: %s", path)
        return path

    def artist_ranking(self, artist_summary: pd.DataFrame, top_n: int = 10) -> Optional[Path]:
        """生成头部艺人上榜曲目数柱状图。"""
        if artist_summary.empty:
            return None
        df = artist_summary.head(top_n).sort_values("total_entries", ascending=True)

        fig, ax = plt.subplots(figsize=(10, 6))
        colors = [self.brand_color] * len(df)
        ax.barh(df["artist"], df["total_entries"], color=colors)
        ax.set_xlabel("上榜曲目数", fontsize=12)
        ax.set_title("头部艺人上榜曲目数统计", fontsize=14, fontweight="bold")
        for i, v in enumerate(df["total_entries"]):
            ax.text(v + 0.1, i, str(v), va="center", fontsize=10)
        ax.set_xlim(0, df["total_entries"].max() * 1.2)
        _apply_font(ax, _CHINESE_FONT_PROP)
        plt.tight_layout()
        return self.save(fig, "chart_artist_ranking.png")

    def platform_new_songs(self, new_songs_count: Dict[str, int]) -> Optional[Path]:
        """生成各平台新歌数量柱状图。"""
        if not new_songs_count:
            return None
        df = pd.DataFrame(list(new_songs_count.items()), columns=["platform", "new_count"])
        df = df.sort_values("new_count", ascending=False)

        fig, ax = plt.subplots(figsize=(8, 5))
        ax.bar(df["platform"], df["new_count"], color=self.secondary_color)
        ax.set_ylabel("新歌数量", fontsize=12)
        ax.set_title("各平台新上榜歌曲数量", fontsize=14, fontweight="bold")
        for i, v in enumerate(df["new_count"]):
            ax.text(i, v + 0.3, str(v), ha="center", fontsize=10)
        ax.set_ylim(0, df["new_count"].max() * 1.2)
        _apply_font(ax, _CHINESE_FONT_PROP)
        plt.tight_layout()
        return self.save(fig, "chart_platform_new_songs.png")

    def cross_platform_hits(self, hits_df: pd.DataFrame, top_n: int = 10) -> Optional[Path]:
        """生成跨平台爆款歌曲上榜平台数柱状图。"""
        if hits_df.empty:
            return None
        df = hits_df.head(top_n).sort_values("platform_count", ascending=True)
        labels = [f"{row['song_name']}\n{row['artist']}" for _, row in df.iterrows()]

        fig, ax = plt.subplots(figsize=(10, 6))
        ax.barh(labels, df["platform_count"], color=self.brand_color)
        ax.set_xlabel("上榜平台数", fontsize=12)
        ax.set_title("跨平台爆款歌曲", fontsize=14, fontweight="bold")
        for i, v in enumerate(df["platform_count"]):
            ax.text(v + 0.05, i, str(v), va="center", fontsize=10)
        ax.set_xlim(0, df["platform_count"].max() * 1.3)
        _apply_font(ax, _CHINESE_FONT_PROP)
        plt.tight_layout()
        return self.save(fig, "chart_cross_platform_hits.png")

    def platform_distribution(self, raw_df: pd.DataFrame) -> Optional[Path]:
        """生成平台歌曲分布饼图。"""
        if raw_df.empty or "platform" not in raw_df.columns:
            return None
        counts = raw_df.groupby("chart_name").size()
        if len(counts) < 2:
            return None

        colors = [self.brand_color, self.secondary_color, self.negative_color, "#4caf50", "#9c27b0"]
        fig, ax = plt.subplots(figsize=(7, 7))
        wedges, texts, autotexts = ax.pie(
            counts.values,
            labels=counts.index,
            autopct="%1.1f%%",
            startangle=90,
            colors=colors[: len(counts)],
            textprops={"fontsize": 11},
        )
        for text in texts + autotexts:
            text.set_fontproperties(_CHINESE_FONT_PROP)
        ax.set_title("各平台榜单歌曲数量分布", fontsize=14, fontweight="bold")
        ax.title.set_fontproperties(_CHINESE_FONT_PROP)
        plt.tight_layout()
        return self.save(fig, "chart_platform_distribution.png")

    def artist_radar(self, artist_summary: pd.DataFrame, top_n: int = 8) -> Optional[Path]:
        """生成头部艺人跨平台覆盖雷达图。"""
        if artist_summary.empty or "platform_count" not in artist_summary.columns:
            return None
        df = artist_summary.head(top_n).copy()
        if df.empty:
            return None

        # 指标：总上榜数、平台数、最佳排名（取倒数，越大越好）
        df["score_rank"] = 1 / (df["best_rank"].replace(0, 1))
        max_entries = df["total_entries"].max() or 1
        df["score_entries"] = df["total_entries"] / max_entries
        max_platform = df["platform_count"].max() or 1
        df["score_platform"] = df["platform_count"] / max_platform

        labels = ["上榜曲目数", "平台覆盖度", "最佳排名"]
        num_vars = len(labels)
        angles = np.linspace(0, 2 * np.pi, num_vars, endpoint=False).tolist()
        angles += angles[:1]

        fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(polar=True))
        for _, row in df.iterrows():
            values = [row["score_entries"], row["score_platform"], row["score_rank"]]
            values += values[:1]
            ax.plot(angles, values, linewidth=1.5, label=row["artist"])
            ax.fill(angles, values, alpha=0.1)

        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(labels, fontproperties=_CHINESE_FONT_PROP)
        ax.set_title("头部艺人综合表现雷达图", fontsize=14, fontweight="bold", pad=20)
        ax.title.set_fontproperties(_CHINESE_FONT_PROP)
        ax.legend(loc="upper right", bbox_to_anchor=(1.3, 1.1), prop=_CHINESE_FONT_PROP)
        plt.tight_layout()
        return self.save(fig, "chart_artist_radar.png")

    def platform_treemap(self, raw_df: pd.DataFrame) -> Optional[Path]:
        """生成歌曲上榜平台数矩形树图。"""
        if raw_df.empty:
            return None
        summary = raw_df.groupby("match_key").agg({
            "song_name": "first",
            "artist": "first",
            "platform": "nunique",
        }).reset_index()
        summary = summary[summary["platform"] >= 1]
        if summary.empty:
            return None

        labels = [f"{row['song_name']}\n({row['platform']}平台)" for _, row in summary.iterrows()]
        sizes = summary["platform"].values
        colors = plt.cm.Blues(np.linspace(0.3, 0.9, len(summary)))

        fig, ax = plt.subplots(figsize=(10, 7))
        squarify.plot(
            sizes=sizes,
            label=labels,
            color=colors,
            alpha=0.8,
            text_kwargs={"fontsize": 8, "fontproperties": _CHINESE_FONT_PROP},
            ax=ax,
        )
        ax.set_title("歌曲上榜平台数矩形树图", fontsize=14, fontweight="bold")
        ax.title.set_fontproperties(_CHINESE_FONT_PROP)
        ax.axis("off")
        plt.tight_layout()
        return self.save(fig, "chart_platform_treemap.png")

    def rank_changes(self, rank_changes_df: pd.DataFrame, top_n: int = 10) -> Optional[Path]:
        """生成排名上升/下降 TOP 变化图。"""
        if rank_changes_df.empty or "rank_change" not in rank_changes_df.columns:
            return None

        df = rank_changes_df.copy()
        df["label"] = df["song_name"] + "\n" + df["artist"]
        # 上升最多
        up = df.nlargest(top_n, "rank_change").sort_values("rank_change", ascending=True)

        fig, ax = plt.subplots(figsize=(10, 6))
        colors = [self.secondary_color if v >= 0 else self.negative_color for v in up["rank_change"]]
        ax.barh(up["label"], up["rank_change"], color=colors)
        ax.set_xlabel("排名变化（上升为正）", fontsize=12)
        ax.set_title("排名上升 TOP 歌曲", fontsize=14, fontweight="bold")
        for i, v in enumerate(up["rank_change"]):
            ax.text(v + 0.5, i, f"+{v}" if v > 0 else str(v), va="center", fontsize=9)
        _apply_font(ax, _CHINESE_FONT_PROP)
        plt.tight_layout()
        return self.save(fig, "chart_rank_changes.png")


def generate_all_charts(analysis: Dict[str, Any], config: Dict[str, Any]) -> List[Path]:
    """根据分析结果生成所有可用图表。"""
    gen = ChartGenerator(config)
    paths = []

    if not analysis["artist_summary"].empty:
        p = gen.artist_ranking(analysis["artist_summary"])
        if p:
            paths.append(p)
        p = gen.artist_radar(analysis["artist_summary"])
        if p:
            paths.append(p)

    if analysis["new_songs_count"]:
        p = gen.platform_new_songs(analysis["new_songs_count"])
        if p:
            paths.append(p)

    if not analysis["cross_platform_hits"].empty:
        p = gen.cross_platform_hits(analysis["cross_platform_hits"])
        if p:
            paths.append(p)

    if not analysis["raw"].empty:
        p = gen.platform_distribution(analysis["raw"])
        if p:
            paths.append(p)
        p = gen.platform_treemap(analysis["raw"])
        if p:
            paths.append(p)

    if not analysis["rank_changes"].empty:
        p = gen.rank_changes(analysis["rank_changes"])
        if p:
            paths.append(p)

    return paths
