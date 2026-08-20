"""Markdown 报告生成。

基于数据与 AI 文案生成 Markdown 格式报告初稿，便于后期转 PPT 或 Word。
"""
import logging
from pathlib import Path
from typing import Any, Dict, List

from src.fetchers.hot_search import format_hot_search_for_report
from src.fetchers.manual_data import (
    format_events_for_report,
    format_industry_for_report,
    format_labels_for_report,
    generate_manual_data_templates,
    load_events,
    load_industry,
    load_labels,
)
from src.utils import OUTPUT_DIR

logger = logging.getLogger("rap_report")


def generate_markdown(
    analysis: Dict[str, Any],
    ai_texts: Dict[str, str],
    chart_paths: List[Path],
    start_date: str,
    end_date: str,
    config: Dict[str, Any],
    hot_search_results: Optional[List[Dict[str, Any]]] = None,
) -> Path:
    """生成 Markdown 报告初稿。"""
    report_cfg = config.get("report", {})
    title = report_cfg.get("title", "说唱音乐行业全景洞察分析报告")
    subtitle = report_cfg.get("subtitle", "深度解析舆情、数据、艺人及产业链趋势（双周版）")

    filename = f"report_{start_date.replace('-', '')}_{end_date.replace('-', '')}.md"
    path = OUTPUT_DIR / filename

    lines: List[str] = []
    lines.append(f"# {title}")
    lines.append(f"\n{subtitle}")
    lines.append(f"\n**报告周期：{start_date} - {end_date}**")
    lines.append("\n---\n")

    # 舆情/热搜总览
    lines.append("## 一、全网舆情与话题总览\n")
    if hot_search_results:
        lines.append(format_hot_search_for_report(hot_search_results))
    else:
        lines.append("（未启用热搜抓取，请人工补充舆情内容）")
    lines.append("\n---\n")

    # 行业动态（手动补充）
    generate_manual_data_templates()
    industry_df = load_industry(config)
    lines.append("## 二、周期内关键行业信息\n")
    lines.append(format_industry_for_report(industry_df))
    lines.append("\n---\n")

    # 概览
    lines.append("## 三、数据概览\n")
    lines.append(f"- 本期共采集 {analysis['total_songs']} 首歌曲")
    lines.append(f"- 涉及 {analysis['total_platforms']} 个平台")
    lines.append(f"- 头部艺人数量：{len(analysis['artist_summary'])}")
    if analysis["new_songs_count"]:
        lines.append("- 各平台新上榜歌曲数量：")
        for platform, count in analysis["new_songs_count"].items():
            lines.append(f"  - {platform}：{count} 首")
    lines.append("\n---\n")

    # 平台榜单总结
    lines.append("## 四、平台榜单总结\n")
    if ai_texts.get("platform_summary"):
        lines.append(ai_texts["platform_summary"])
    else:
        lines.append("（AI 文案未生成，请根据下方数据手动补充）")
    lines.append("\n")

    # 各平台 TOP10
    raw = analysis["raw"]
    if not raw.empty:
        for chart_name, group in raw.groupby("chart_name"):
            lines.append(f"### {chart_name} TOP10\n")
            top10 = group.nsmallest(10, "rank")[["rank", "song_name", "artist"]]
            lines.append("| 排名 | 歌曲 | 艺人 |")
            lines.append("| --- | --- | --- |")
            for _, row in top10.iterrows():
                lines.append(f"| {row['rank']} | {row['song_name']} | {row['artist']} |")
            lines.append("\n")

    # 头部艺人
    lines.append("## 五、头部艺人表现\n")
    if ai_texts.get("artist_insight"):
        lines.append(ai_texts["artist_insight"])
    else:
        lines.append("（AI 文案未生成，请根据下方数据手动补充）")
    lines.append("\n")
    if not analysis["artist_summary"].empty:
        lines.append("| 艺人 | 总上榜数 | 平台数 | 最佳排名 | 最佳歌曲 |")
        lines.append("| --- | --- | --- | --- | --- |")
        for _, row in analysis["artist_summary"].head(15).iterrows():
            lines.append(
                f"| {row['artist']} | {row['total_entries']} | {row['platform_count']} | {row['best_rank']} | {row['best_song']} |"
            )
        lines.append("\n")

    # 跨平台爆款
    lines.append("## 六、跨平台爆款歌曲\n")
    if ai_texts.get("hit_songs_insight"):
        lines.append(ai_texts["hit_songs_insight"])
    else:
        lines.append("（AI 文案未生成，请根据下方数据手动补充）")
    lines.append("\n")
    if not analysis["cross_platform_hits"].empty:
        lines.append("| 歌曲 | 艺人 | 上榜平台数 | 最佳排名 |")
        lines.append("| --- | --- | --- | --- |")
        for _, row in analysis["cross_platform_hits"].iterrows():
            lines.append(
                f"| {row['song_name']} | {row['artist']} | {row['platform_count']} | {row['best_rank']} |"
            )
        lines.append("\n")
    else:
        lines.append("本期暂无跨平台爆款歌曲。\n")

    # 演出信息（手动补充）
    events_df = load_events(config)
    lines.append("## 七、演出与市场动态\n")
    lines.append(format_events_for_report(events_df))
    lines.append("\n---\n")

    # 厂牌信息（手动补充）
    labels_df = load_labels(config)
    lines.append("## 八、代表厂牌深度解析\n")
    lines.append(format_labels_for_report(labels_df))
    lines.append("\n---\n")

    # 图表
    if chart_paths:
        lines.append("## 九、可视化图表\n")
        for chart_path in chart_paths:
            rel_path = chart_path.name
            lines.append(f"### {chart_path.stem}")
            lines.append(f"![{chart_path.stem}]({rel_path})")
            lines.append("\n")

    # 待人工补充
    lines.append("---\n")
    lines.append("## 十、待人工补充内容\n")
    lines.append("- [ ] 正面/中性/负面舆情关注点细分")
    lines.append("- [ ] 艺人动态与商业变现细节")
    lines.append("- [ ] 产业链与资本动态")
    lines.append("- [ ] 政策监管与合规")
    lines.append("- [ ] 风险机遇与策略建议")
    lines.append("\n---\n")
    lines.append("*本报告由自动化工具生成，分析文案为 AI 初稿，发布前请人工审核。*")

    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    logger.info("Markdown 报告已保存: %s", path)
    return path
