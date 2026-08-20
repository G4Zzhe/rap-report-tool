"""图表生成模块。

使用 matplotlib 生成报告中需要的静态图表：
- 头部艺人上榜曲目数柱状图
- 各平台新歌数量柱状图
- 跨平台爆款歌曲数量对比
- 地区分布饼图（全球榜）
"""
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

import matplotlib
import matplotlib.font_manager as fm
import matplotlib.pyplot as plt
import pandas as pd

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

    def region_distribution(self, region_data: Dict[str, int]) -> Optional[Path]:
        """生成地区分布饼图（用于全球榜）。"""
        if not region_data:
            return None
        labels = list(region_data.keys())
        sizes = list(region_data.values())
        colors = ["#1f4e99", "#f5a623", "#e94b3c", "#4caf50", "#9c27b0"]

        fig, ax = plt.subplots(figsize=(7, 7))
        wedges, texts, autotexts = ax.pie(
            sizes,
            labels=labels,
            autopct="%1.0f%%",
            startangle=90,
            colors=colors[: len(labels)],
            textprops={"fontsize": 11},
        )
        # 饼图文字应用字体
        for text in texts + autotexts:
            text.set_fontproperties(_CHINESE_FONT_PROP)
        ax.set_title("TOP50 地区分布", fontsize=14, fontweight="bold")
        ax.title.set_fontproperties(_CHINESE_FONT_PROP)
        plt.tight_layout()
        return self.save(fig, "chart_region_distribution.png")


def generate_all_charts(analysis: Dict[str, Any], config: Dict[str, Any]) -> List[Path]:
    """根据分析结果生成所有可用图表。"""
    gen = ChartGenerator(config)
    paths = []

    if not analysis["artist_summary"].empty:
        p = gen.artist_ranking(analysis["artist_summary"])
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

    return paths
