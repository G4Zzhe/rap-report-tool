"""主入口脚本。

用法：
    python run.py --start 2026-07-16 --end 2026-07-31

未指定日期时默认使用上一双周周期。
"""
import argparse
import logging
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

# 将项目根目录加入 Python 路径
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.ai.writer import AIWriter
from src.analysis.aggregator import analyze
from src.charts.generator import generate_all_charts
from src.fetchers import fetch_all, fetch_all_hot_search
from src.report.excel import generate_excel
from src.report.markdown import generate_markdown
from src.report.pptx import generate_pptx
from src.utils import load_config, setup_logging

logger = setup_logging()


def default_biweekly_range() -> tuple[str, str]:
    """默认返回上一完整的双周周期。"""
    today = datetime.now()
    # 找到本月 1 号或 16 号作为周期起点
    if today.day >= 16:
        start = today.replace(day=1)
        end = today.replace(day=15)
    else:
        # 上个月的 16 号到月底
        last_month = today.replace(day=1) - timedelta(days=1)
        start = last_month.replace(day=16)
        end = last_month.replace(day=last_month.day)
    return start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="说唱音乐行业双周报自动化工具")
    parser.add_argument(
        "--start",
        type=str,
        help="报告周期开始日期，格式 YYYY-MM-DD",
    )
    parser.add_argument(
        "--end",
        type=str,
        help="报告周期结束日期，格式 YYYY-MM-DD",
    )
    parser.add_argument(
        "--history",
        type=str,
        help="上一期原始榜单 CSV 路径，用于计算新歌和排名变化",
    )
    parser.add_argument(
        "--no-ai",
        action="store_true",
        help="禁用 AI 文案生成（无需 API Key，生成报告骨架）",
    )
    return parser.parse_args()


def load_history(args: argparse.Namespace) -> Optional[List[Dict[str, Any]]]:
    """加载历史榜单数据（CSV 格式）。"""
    if not args.history:
        return None
    import pandas as pd

    path = Path(args.history)
    if not path.exists():
        logger.warning("历史数据文件不存在: %s", path)
        return None
    df = pd.read_csv(path)
    # 转换为 aggregator 需要的列表结构
    results: Dict[str, List[Dict[str, Any]]] = {}
    for _, row in df.iterrows():
        platform = row["platform"]
        results.setdefault(platform, {
            "platform": platform,
            "chart_name": row["chart_name"],
            "tracks": [],
        })
        results[platform]["tracks"].append({
            "rank": int(row["rank"]),
            "song_name": row["song_name"],
            "artist": row["artist"],
            "album": row.get("album", ""),
            "is_new": bool(row.get("is_new", False)),
        })
    return list(results.values())


def main() -> int:
    args = parse_args()
    start_date = args.start or default_biweekly_range()[0]
    end_date = args.end or default_biweekly_range()[1]

    logger.info("开始生成报告：%s 至 %s", start_date, end_date)

    config = load_config()

    try:
        # 1. 抓取榜单数据
        results = fetch_all(config)

        # 2. 抓取热搜数据
        hot_search_results = fetch_all_hot_search(config)

        # 3. 保存原始数据 CSV
        import pandas as pd
        raw_frames = []
        for r in results:
            if r.get("tracks"):
                raw_frames.append(
                    pd.DataFrame(r["tracks"]).assign(
                        platform=r["platform"], chart_name=r["chart_name"]
                    )
                )
        if raw_frames:
            raw_df = pd.concat(raw_frames, ignore_index=True)
        else:
            raw_df = pd.DataFrame()
        raw_csv_path = PROJECT_ROOT / "output" / f"raw_{start_date.replace('-', '')}_{end_date.replace('-', '')}.csv"
        raw_df.to_csv(raw_csv_path, index=False, encoding="utf-8-sig")
        logger.info("原始数据已保存: %s", raw_csv_path)

        # 4. 加载历史数据并分析
        history_results = load_history(args)
        analysis = analyze(results, history_results)

        # 5. 生成 AI 文案
        if args.no_ai:
            logger.info("已禁用 AI 文案生成")
            ai_texts = {
                "platform_summary": "",
                "artist_insight": "",
                "hit_songs_insight": "",
            }
        else:
            ai_writer = AIWriter(config)
            ai_texts = ai_writer.generate_all(analysis)

        # 6. 生成图表
        chart_paths = generate_all_charts(analysis, config)

        # 7. 生成 Excel
        excel_path = generate_excel(analysis, start_date, end_date)

        # 8. 生成 Markdown
        md_path = generate_markdown(
            analysis, ai_texts, chart_paths, start_date, end_date, config,
            hot_search_results=hot_search_results,
        )

        # 9. 生成 PPT
        pptx_path = generate_pptx(analysis, ai_texts, chart_paths, start_date, end_date, config)
    except Exception as e:
        logger.exception("报告生成流程失败: %s", e)
        print(f"\n报告生成失败: {e}")
        return 1

    logger.info("全部完成！")
    logger.info("Markdown: %s", md_path)
    logger.info("Excel: %s", excel_path)
    logger.info("PPT: %s", pptx_path)
    logger.info("CSV: %s", raw_csv_path)
    for p in chart_paths:
        logger.info("Chart: %s", p)

    # 输出摘要到控制台
    print("\n=== 报告生成完成 ===")
    print(f"周期：{start_date} - {end_date}")
    print(f"Markdown：{md_path}")
    print(f"Excel：{excel_path}")
    print(f"PPT：{pptx_path}")
    print(f"CSV：{raw_csv_path}")
    print("图表：")
    for p in chart_paths:
        print(f"  - {p}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
