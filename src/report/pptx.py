"""PPT 报告生成。

读取公司 PPT 模板，基于数据、AI 文案和图表自动填充以下内容：
- 封面（标题、副标题、周期）
- 数据概览
- 平台榜单总结 + 各平台 TOP10
- 头部艺人表现
- 跨平台爆款
- 可视化图表页
- 待人工补充的章节提示页

其余页面保留模板原有内容，供人工后续补充。
"""
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Inches, Pt

from src.utils import OUTPUT_DIR

logger = logging.getLogger("rap_report")

# 默认模板路径可在 config.yaml 的 pptx.template_path 中覆盖
DEFAULT_TEMPLATE_PATH = None

# 配色方案（与公司模板主色调对齐）
PRIMARY_COLOR = RGBColor(31, 78, 153)      # 深蓝
SECONDARY_COLOR = RGBColor(245, 166, 35)   # 橙黄
ACCENT_RED = RGBColor(233, 75, 60)         # 红色强调
TEXT_DARK = RGBColor(51, 51, 51)           # 深灰正文
TEXT_LIGHT = RGBColor(255, 255, 255)       # 白色
BG_LIGHT = RGBColor(240, 244, 248)         # 浅灰背景


def _format_period(start_date: str, end_date: str) -> str:
    """格式化为中文周期字符串。"""
    try:
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
        return f"报告周期：{start.year}年{start.month}月{start.day}日 - {end.month}月{end.day}日"
    except ValueError:
        return f"报告周期：{start_date} - {end_date}"


def _get_blank_layout(prs: Presentation):
    """获取空白布局，兼容不同模板。"""
    for layout in prs.slide_layouts:
        if "空白" in layout.name or "blank" in layout.name.lower():
            return layout
    return prs.slide_layouts[-1]


def _add_text_box(
    slide,
    left: float,
    top: float,
    width: float,
    height: float,
    text: str,
    font_size: int = 18,
    bold: bool = False,
    color: RGBColor = TEXT_DARK,
    align: PP_ALIGN = PP_ALIGN.LEFT,
    font_name: str = "Microsoft YaHei",
) -> Any:
    """统一添加文本框并设置格式。

    当文本可能过长时，自动减小字号以避免溢出。
    """
    box = slide.shapes.add_textbox(Inches(left), Inches(top), Inches(width), Inches(height))
    tf = box.text_frame
    tf.word_wrap = True
    tf.auto_size = None  # 不自动调整文本框大小
    p = tf.paragraphs[0]
    p.text = text
    p.font.size = Pt(font_size)
    p.font.bold = bold
    p.font.color.rgb = color
    p.font.name = font_name
    p.alignment = align

    # 粗略溢出检测：按每行可容纳字符数估算
    max_chars_per_line = int(width * 40 / (font_size / 12))
    max_lines = max(1, int(height * 25 / (font_size / 12)))
    total_chars = len(text)
    estimated_lines = max(1, total_chars / max_chars_per_line)
    if estimated_lines > max_lines and font_size > 10:
        new_size = max(10, int(font_size * max_lines / estimated_lines))
        p.font.size = Pt(new_size)
    return box


def _add_title_slide(prs: Presentation, title: str, subtitle: str, period: str) -> None:
    """添加封面页。"""
    layout = _get_blank_layout(prs)
    slide = prs.slides.add_slide(layout)

    # 顶部装饰条
    bar = slide.shapes.add_shape(
        1, Inches(0), Inches(0), Inches(10), Inches(0.15)
    )
    bar.fill.solid()
    bar.fill.fore_color.rgb = SECONDARY_COLOR
    bar.line.fill.background()

    _add_text_box(
        slide, 0.8, 2.0, 8.4, 1.4,
        title, font_size=44, bold=True, color=PRIMARY_COLOR, align=PP_ALIGN.CENTER
    )
    _add_text_box(
        slide, 0.8, 3.6, 8.4, 0.8,
        subtitle, font_size=20, bold=False, color=TEXT_DARK, align=PP_ALIGN.CENTER
    )
    _add_text_box(
        slide, 0.8, 4.7, 8.4, 0.5,
        period, font_size=18, bold=False, color=RGBColor(100, 100, 100), align=PP_ALIGN.CENTER
    )

    # 底部提示
    _add_text_box(
        slide, 0.8, 6.6, 8.4, 0.5,
        "本报告由自动化工具生成，分析文案为 AI 初稿，发布前请人工审核。",
        font_size=12, color=RGBColor(150, 150, 150), align=PP_ALIGN.CENTER
    )


def _add_section_header(slide, title: str) -> None:
    """为页面添加统一的章节标题栏。"""
    # 左侧色块
    accent = slide.shapes.add_shape(
        1, Inches(0.4), Inches(0.45), Inches(0.12), Inches(0.65)
    )
    accent.fill.solid()
    accent.fill.fore_color.rgb = SECONDARY_COLOR
    accent.line.fill.background()

    _add_text_box(
        slide, 0.7, 0.45, 8.5, 0.7,
        title, font_size=28, bold=True, color=PRIMARY_COLOR
    )


def _add_overview_slide(prs: Presentation, analysis: Dict[str, Any], start_date: str, end_date: str) -> None:
    """添加数据概览页。"""
    layout = _get_blank_layout(prs)
    slide = prs.slides.add_slide(layout)
    _add_section_header(slide, "数据概览")

    stats = [
        ("本期采集歌曲", f"{analysis['total_songs']} 首", PRIMARY_COLOR),
        ("涉及平台", f"{analysis['total_platforms']} 个", SECONDARY_COLOR),
        ("头部艺人数量", f"{len(analysis['artist_summary'])}", PRIMARY_COLOR),
        ("跨平台爆款", f"{len(analysis['cross_platform_hits'])} 首", SECONDARY_COLOR),
        ("报告周期", f"{start_date} 至 {end_date}", TEXT_DARK),
    ]

    top = 1.5
    for label, value, color in stats:
        # 卡片背景
        card = slide.shapes.add_shape(
            1, Inches(0.8), Inches(top), Inches(8.4), Inches(0.75)
        )
        card.fill.solid()
        card.fill.fore_color.rgb = BG_LIGHT
        card.line.color.rgb = RGBColor(220, 220, 220)

        _add_text_box(slide, 1.0, top + 0.15, 4.0, 0.5, label, font_size=18, color=TEXT_DARK)
        _add_text_box(
            slide, 5.5, top + 0.1, 3.5, 0.6,
            value, font_size=24, bold=True, color=color, align=PP_ALIGN.RIGHT
        )
        top += 1.0


def _add_platform_summary_slide(
    prs: Presentation,
    analysis: Dict[str, Any],
    ai_texts: Dict[str, str],
) -> None:
    """添加平台榜单总结页。"""
    layout = _get_blank_layout(prs)
    slide = prs.slides.add_slide(layout)
    _add_section_header(slide, "平台榜单总结")

    content = ai_texts.get("platform_summary") or "（AI 文案未生成）"
    content = content.replace("**", "")

    _add_text_box(
        slide, 0.7, 1.4, 8.6, 5.2,
        content, font_size=16, color=TEXT_DARK
    )


def _style_table_header(table, cols: int) -> None:
    """统一设置表头样式。"""
    for col in range(cols):
        cell = table.cell(0, col)
        cell.fill.solid()
        cell.fill.fore_color.rgb = PRIMARY_COLOR
        p = cell.text_frame.paragraphs[0]
        p.font.color.rgb = TEXT_LIGHT
        p.font.bold = True
        p.font.size = Pt(12)


def _add_top10_slides(prs: Presentation, analysis: Dict[str, Any]) -> None:
    """为每个榜单添加 TOP10 页。"""
    raw = analysis.get("raw")
    if raw is None or raw.empty:
        return

    for chart_name, group in raw.groupby("chart_name"):
        layout = _get_blank_layout(prs)
        slide = prs.slides.add_slide(layout)
        _add_section_header(slide, f"{chart_name} TOP10")

        top10 = group.nsmallest(10, "rank")[["rank", "song_name", "artist"]]
        rows = len(top10)
        cols = 3
        left = Inches(0.7)
        top = Inches(1.35)
        width = Inches(8.6)
        height = Inches(0.45 * rows + 0.2)

        table = slide.shapes.add_table(rows + 1, cols, left, top, width, height).table
        _style_table_header(table, cols)

        headers = ["排名", "歌曲", "艺人"]
        for i, header in enumerate(headers):
            table.cell(0, i).text = header

        for idx, (_, row) in enumerate(top10.iterrows(), start=1):
            table.cell(idx, 0).text = str(int(row["rank"]))
            table.cell(idx, 1).text = str(row["song_name"])
            table.cell(idx, 2).text = str(row["artist"])
            for col in range(cols):
                cell = table.cell(idx, col)
                p = cell.text_frame.paragraphs[0]
                p.font.size = Pt(11)
                p.font.color.rgb = TEXT_DARK


def _add_artist_slide(prs: Presentation, analysis: Dict[str, Any], ai_texts: Dict[str, str]) -> None:
    """添加头部艺人表现页。"""
    layout = _get_blank_layout(prs)
    slide = prs.slides.add_slide(layout)
    _add_section_header(slide, "头部艺人表现")

    content = ai_texts.get("artist_insight") or "（AI 文案未生成）"
    content = content.replace("**", "")

    _add_text_box(
        slide, 0.7, 1.3, 8.6, 1.6,
        content, font_size=15, color=TEXT_DARK
    )

    artist_df = analysis["artist_summary"].head(10)
    if artist_df.empty:
        return

    rows = len(artist_df)
    cols = 5
    left = Inches(0.4)
    top = Inches(3.1)
    width = Inches(9.2)
    height = Inches(0.38 * rows + 0.2)

    table = slide.shapes.add_table(rows + 1, cols, left, top, width, height).table
    _style_table_header(table, cols)

    headers = ["艺人", "总上榜数", "平台数", "最佳排名", "最佳歌曲"]
    for i, header in enumerate(headers):
        table.cell(0, i).text = header

    for idx, (_, row) in enumerate(artist_df.iterrows(), start=1):
        table.cell(idx, 0).text = str(row["artist"])
        table.cell(idx, 1).text = str(int(row["total_entries"]))
        table.cell(idx, 2).text = str(int(row["platform_count"]))
        table.cell(idx, 3).text = str(int(row["best_rank"]))
        table.cell(idx, 4).text = str(row["best_song"])
        for col in range(cols):
            cell = table.cell(idx, col)
            p = cell.text_frame.paragraphs[0]
            p.font.size = Pt(10)
            p.font.color.rgb = TEXT_DARK


def _add_hit_songs_slide(prs: Presentation, analysis: Dict[str, Any], ai_texts: Dict[str, str]) -> None:
    """添加跨平台爆款页。"""
    layout = _get_blank_layout(prs)
    slide = prs.slides.add_slide(layout)
    _add_section_header(slide, "跨平台爆款歌曲")

    content = ai_texts.get("hit_songs_insight") or "（AI 文案未生成）"
    content = content.replace("**", "")

    _add_text_box(
        slide, 0.7, 1.3, 8.6, 1.4,
        content, font_size=15, color=TEXT_DARK
    )

    hits_df = analysis["cross_platform_hits"]
    if hits_df.empty:
        _add_text_box(
            slide, 0.7, 3.0, 8.6, 0.8,
            "本期暂无跨平台爆款歌曲。", font_size=18, color=TEXT_DARK
        )
        return

    rows = len(hits_df)
    cols = 4
    left = Inches(0.8)
    top = Inches(2.9)
    width = Inches(8.4)
    height = Inches(0.45 * rows + 0.2)

    table = slide.shapes.add_table(rows + 1, cols, left, top, width, height).table
    _style_table_header(table, cols)

    headers = ["歌曲", "艺人", "上榜平台数", "最佳排名"]
    for i, header in enumerate(headers):
        table.cell(0, i).text = header

    for idx, (_, row) in enumerate(hits_df.iterrows(), start=1):
        table.cell(idx, 0).text = str(row["song_name"])
        table.cell(idx, 1).text = str(row["artist"])
        table.cell(idx, 2).text = str(int(row["platform_count"]))
        table.cell(idx, 3).text = str(int(row["best_rank"]))
        for col in range(cols):
            cell = table.cell(idx, col)
            p = cell.text_frame.paragraphs[0]
            p.font.size = Pt(11)
            p.font.color.rgb = TEXT_DARK


def _add_chart_slides(prs: Presentation, chart_paths: List[Path]) -> None:
    """为每个图表添加一页，避免图片溢出。"""
    for chart_path in chart_paths:
        if not chart_path.exists():
            continue
        layout = _get_blank_layout(prs)
        slide = prs.slides.add_slide(layout)

        title = chart_path.stem.replace("chart_", "").replace("_", " ").title()
        _add_section_header(slide, title)

        # 安全区域：标题栏占 0.45~1.2，图片从 1.3 开始，底部留 0.3
        available_height = 7.5 - 1.3 - 0.3  # 5.9 inches
        available_width = 10 - 1.0 - 1.0  # 8 inches
        slide.shapes.add_picture(
            str(chart_path),
            Inches(1.0),
            Inches(1.3),
            width=Inches(min(8.0, available_width)),
            height=Inches(min(5.5, available_height)),
        )


def _add_placeholder_slide(prs: Presentation, section: str, items: List[str]) -> None:
    """添加待人工补充的章节提示页。"""
    layout = _get_blank_layout(prs)
    slide = prs.slides.add_slide(layout)
    _add_section_header(slide, f"{section}（待补充）")

    top = 1.5
    for item in items:
        _add_text_box(
            slide, 0.9, top, 8.4, 0.5,
            f"• {item}", font_size=18, color=TEXT_DARK
        )
        top += 0.65

    _add_text_box(
        slide, 0.9, top + 0.3, 8.4, 0.8,
        "提示：此部分数据目前依赖人工整理，可在后续版本中接入舆情/厂牌/演出等数据源。",
        font_size=14, color=RGBColor(150, 150, 150)
    )


def generate_pptx(
    analysis: Dict[str, Any],
    ai_texts: Dict[str, str],
    chart_paths: List[Path],
    start_date: str,
    end_date: str,
    config: Dict[str, Any],
    template_path: Optional[Path] = None,
) -> Path:
    """生成 PPT 报告初稿。

    优先使用公司模板；若模板不可用，则创建一个包含基础页面的新演示文稿。
    """
    report_cfg = config.get("report", {})
    pptx_cfg = config.get("pptx", {})
    title = report_cfg.get("title", "说唱音乐行业全景洞察分析报告")
    subtitle = report_cfg.get("subtitle", "深度解析舆情、数据、艺人及产业链趋势（双周版）")
    period = _format_period(start_date, end_date)

    template = template_path or pptx_cfg.get("template_path") or DEFAULT_TEMPLATE_PATH
    if template:
        template = Path(template)
    if template and template.exists():
        prs = Presentation(str(template))
        logger.info("使用 PPT 模板: %s", template)
    else:
        prs = Presentation()
        prs.slide_width = Inches(10)
        prs.slide_height = Inches(7.5)
        if template:
            logger.warning("PPT 模板未找到，使用空白演示文稿: %s", template)
        else:
            logger.info("未配置 PPT 模板，使用内置通用版式")

    _add_title_slide(prs, title, subtitle, period)
    _add_overview_slide(prs, analysis, start_date, end_date)
    _add_platform_summary_slide(prs, analysis, ai_texts)
    _add_top10_slides(prs, analysis)
    _add_artist_slide(prs, analysis, ai_texts)
    _add_hit_songs_slide(prs, analysis, ai_texts)
    _add_chart_slides(prs, chart_paths)

    _add_placeholder_slide(
        prs,
        "舆情与话题",
        ["全网舆情与话题总览", "正面/中性/负面舆情关注点"],
    )
    _add_placeholder_slide(
        prs,
        "厂牌与行业",
        ["代表厂牌深度解析", "周期内关键行业信息", "艺人动态与商业变现"],
    )
    _add_placeholder_slide(
        prs,
        "产业与风险",
        ["产业链与资本动态", "政策监管与合规", "风险机遇与策略建议"],
    )

    filename = f"report_{start_date.replace('-', '')}_{end_date.replace('-', '')}.pptx"
    path = OUTPUT_DIR / filename
    prs.save(str(path))
    logger.info("PPT 报告已保存: %s", path)
    return path
