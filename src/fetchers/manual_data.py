"""演出/厂牌手动数据读取模块。

由于演出信息、厂牌数据没有稳定公开的免费 API，本模块支持通过 CSV 文件手动维护，
工具读取后生成报告中的"艺人动态与商业变现"、"代表厂牌深度解析"、"周期内关键行业信息"等章节。

CSV 文件位置（可配置）：
- data/events.csv：演出信息
- data/labels.csv：厂牌信息
- data/industry.csv：行业动态/舆情补充
"""
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

from src.utils import OUTPUT_DIR, ROOT_DIR

logger = logging.getLogger("rap_report")

DEFAULT_DATA_DIR = ROOT_DIR / "data"


def _read_csv_if_exists(path: Path) -> pd.DataFrame:
    """读取 CSV 文件，不存在则返回空 DataFrame。"""
    if not path.exists():
        return pd.DataFrame()
    try:
        return pd.read_csv(path, encoding="utf-8-sig")
    except Exception as e:
        logger.warning("读取 %s 失败: %s", path, e)
        return pd.DataFrame()


def load_events(config: Dict[str, Any]) -> pd.DataFrame:
    """加载演出信息。"""
    cfg = config.get("manual_data", {})
    path = Path(cfg.get("events_path", DEFAULT_DATA_DIR / "events.csv"))
    df = _read_csv_if_exists(path)
    if not df.empty:
        logger.info("已加载 %d 条演出信息", len(df))
    return df


def load_labels(config: Dict[str, Any]) -> pd.DataFrame:
    """加载厂牌信息。"""
    cfg = config.get("manual_data", {})
    path = Path(cfg.get("labels_path", DEFAULT_DATA_DIR / "labels.csv"))
    df = _read_csv_if_exists(path)
    if not df.empty:
        logger.info("已加载 %d 条厂牌信息", len(df))
    return df


def load_industry(config: Dict[str, Any]) -> pd.DataFrame:
    """加载行业动态/舆情补充数据。"""
    cfg = config.get("manual_data", {})
    path = Path(cfg.get("industry_path", DEFAULT_DATA_DIR / "industry.csv"))
    df = _read_csv_if_exists(path)
    if not df.empty:
        logger.info("已加载 %d 条行业动态", len(df))
    return df


def format_events_for_report(df: pd.DataFrame) -> str:
    """将演出信息格式化为 Markdown。"""
    if df.empty:
        return "（暂无演出信息，可在 data/events.csv 中补充）"
    lines = []
    for _, row in df.iterrows():
        date = row.get("date", "")
        name = row.get("name", "未知演出")
        city = row.get("city", "")
        venue = row.get("venue", "")
        artists = row.get("artists", "")
        status = row.get("status", "")
        parts = [p for p in [date, city, venue, artists, status] if p]
        lines.append(f"- **{name}**" + ("：" + " / ".join(parts) if parts else ""))
    return "\n".join(lines)


def format_labels_for_report(df: pd.DataFrame) -> str:
    """将厂牌信息格式化为 Markdown。"""
    if df.empty:
        return "（暂无厂牌信息，可在 data/labels.csv 中补充）"
    lines = []
    for _, row in df.iterrows():
        name = row.get("name", "未知厂牌")
        focus = row.get("focus", "")
        artists = row.get("artists", "")
        highlight = row.get("highlight", "")
        parts = [p for p in [focus, artists, highlight] if p]
        lines.append(f"- **{name}**" + ("：" + " / ".join(parts) if parts else ""))
    return "\n".join(lines)


def format_industry_for_report(df: pd.DataFrame) -> str:
    """将行业动态格式化为 Markdown。"""
    if df.empty:
        return "（暂无行业动态，可在 data/industry.csv 中补充）"
    lines = []
    for _, row in df.iterrows():
        category = row.get("category", "")
        title = row.get("title", "")
        summary = row.get("summary", "")
        if category:
            lines.append(f"- **[{category}] {title}**：{summary}")
        else:
            lines.append(f"- **{title}**：{summary}")
    return "\n".join(lines)


def _df_to_bullet_rows(df: pd.DataFrame, columns: List[str], title_col: str) -> List[Tuple[str, str]]:
    """将 DataFrame 转换为（标题，详情）列表，供 PPT 使用。"""
    rows = []
    for _, row in df.iterrows():
        title = str(row.get(title_col, "")).strip()
        if not title:
            continue
        details = " / ".join([str(row.get(c, "")).strip() for c in columns if str(row.get(c, "")).strip() and c != title_col])
        rows.append((title, details))
    return rows


def get_events_for_ppt(df: pd.DataFrame) -> List[Tuple[str, str]]:
    """返回演出信息（标题，详情），供 PPT 使用。"""
    if df.empty:
        return []
    return _df_to_bullet_rows(df, ["date", "city", "venue", "artists", "status"], "name")


def get_labels_for_ppt(df: pd.DataFrame) -> List[Tuple[str, str]]:
    """返回厂牌信息（标题，详情），供 PPT 使用。"""
    if df.empty:
        return []
    return _df_to_bullet_rows(df, ["focus", "artists", "highlight"], "name")


def get_industry_for_ppt(df: pd.DataFrame) -> List[Tuple[str, str]]:
    """返回行业动态（标题，详情），供 PPT 使用。"""
    if df.empty:
        return []
    rows = []
    for _, row in df.iterrows():
        category = str(row.get("category", "")).strip()
        title = str(row.get("title", "")).strip()
        summary = str(row.get("summary", "")).strip()
        if not title:
            continue
        display_title = f"[{category}] {title}" if category else title
        rows.append((display_title, summary))
    return rows


def generate_manual_data_templates() -> None:
    """生成示例 CSV 模板文件。"""
    DEFAULT_DATA_DIR.mkdir(exist_ok=True)

    events_template = DEFAULT_DATA_DIR / "events.csv"
    if not events_template.exists():
        pd.DataFrame([
            {"date": "2026-07-20", "name": "示例说唱音乐节", "city": "成都", "venue": "东郊记忆", "artists": "GAI/马思唯", "status": "已开票"},
        ]).to_csv(events_template, index=False, encoding="utf-8-sig")
        logger.info("生成演出信息模板: %s", events_template)

    labels_template = DEFAULT_DATA_DIR / "labels.csv"
    if not labels_template.exists():
        pd.DataFrame([
            {"name": "示例厂牌", "focus": "成都说唱", "artists": "GAI/马思唯/KnowKnow", "highlight": "本周期发布新专辑"},
        ]).to_csv(labels_template, index=False, encoding="utf-8-sig")
        logger.info("生成厂牌信息模板: %s", labels_template)

    industry_template = DEFAULT_DATA_DIR / "industry.csv"
    if not industry_template.exists():
        pd.DataFrame([
            {"category": "综艺", "title": "《说唱巅峰对决2026》热播", "summary": "本周期节目话题量持续增长"},
        ]).to_csv(industry_template, index=False, encoding="utf-8-sig")
        logger.info("生成行业动态模板: %s", industry_template)
