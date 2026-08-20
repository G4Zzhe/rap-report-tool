"""Excel 报告生成。

将原始榜单数据、聚合分析结果写入一个 Excel 文件，包含多个 sheet：
- 原始数据
- 艺人汇总
- 歌曲汇总
- 跨平台爆款
- 排名变化（如有历史数据）
"""
import logging
from pathlib import Path
from typing import Any, Dict

import pandas as pd

from src.utils import OUTPUT_DIR

logger = logging.getLogger("rap_report")


def generate_excel(analysis: Dict[str, Any], start_date: str, end_date: str) -> Path:
    """生成 Excel 分析报告。"""
    filename = f"analysis_{start_date.replace('-', '')}_{end_date.replace('-', '')}.xlsx"
    path = OUTPUT_DIR / filename

    with pd.ExcelWriter(path, engine="openpyxl") as writer:  # type: ignore[assignment]
        analysis["raw"].to_excel(writer, sheet_name="原始榜单数据", index=False)

        if not analysis["artist_summary"].empty:
            analysis["artist_summary"].to_excel(writer, sheet_name="艺人汇总", index=False)
        if not analysis["song_summary"].empty:
            analysis["song_summary"].to_excel(writer, sheet_name="歌曲汇总", index=False)
        if not analysis["cross_platform_hits"].empty:
            analysis["cross_platform_hits"].to_excel(writer, sheet_name="跨平台爆款", index=False)
        if not analysis["rank_changes"].empty:
            analysis["rank_changes"].to_excel(writer, sheet_name="排名变化", index=False)

        # 新增一个统计概览 sheet
        overview = {
            "指标": ["总歌曲数", "涉及平台数", "头部艺人数量"],
            "数值": [
                analysis["total_songs"],
                analysis["total_platforms"],
                len(analysis["artist_summary"]),
            ],
        }
        pd.DataFrame(overview).to_excel(writer, sheet_name="概览", index=False)

    logger.info("Excel 报告已保存: %s", path)
    return path
