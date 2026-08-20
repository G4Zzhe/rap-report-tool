"""微博/抖音热搜基础抓取模块。

由于微博、抖音的反爬策略较强，本模块采用"公开接口优先 + 降级提示"策略：
- 抖音热榜：使用公开接口 https://www.douyin.com/aweme/v1/web/hot/search/list/
- 微博热搜：需要有效的登录 Cookie，当前仅返回占位提示

抓取结果用于报告中的"全网舆情与话题总览"章节，作为人工补充的参考。
"""
import logging
from typing import Any, Dict, List

import requests

from src.utils import get_headers

logger = logging.getLogger("rap_report")

# 默认说唱相关关键词
DEFAULT_RAP_KEYWORDS = [
    "说唱", "嘻哈", "rap", "Rap", "RAP", "Rapper", "rapper",
    "厂牌", " diss ", "Diss", "freestyle", "Freestyle", "中国新说唱",
    "说唱巅峰对决", " listenup ", "地下八英里",
]

DOUYIN_HOT_URL = "https://www.douyin.com/aweme/v1/web/hot/search/list/"


class HotSearchFetcher:
    """热搜抓取器。"""

    def __init__(self, keywords: List[str] = None) -> None:
        self.keywords = keywords or DEFAULT_RAP_KEYWORDS
        self.session = requests.Session()
        self.session.headers.update(get_headers())

    def fetch_douyin(self) -> Dict[str, Any]:
        """抓取抖音热榜并筛选说唱相关内容。"""
        result: Dict[str, Any] = {
            "platform": "douyin",
            "topics": [],
            "success": False,
            "error": None,
        }
        try:
            self.session.headers.update({
                "Referer": "https://www.douyin.com/",
            })
            resp = self.session.get(DOUYIN_HOT_URL, timeout=15)
            resp.raise_for_status()
            data = resp.json()
            items = data.get("data", {}).get("word_list", [])
            topics = []
            for item in items:
                word = item.get("word", "")
                if any(k in word for k in self.keywords):
                    topics.append({
                        "rank": item.get("position"),
                        "topic": word,
                        "hot_value": item.get("hot_value"),
                        "label": item.get("label", ""),
                    })
            result["topics"] = topics
            result["success"] = True
            logger.info("抖音热榜抓取完成，共 %d 条，说唱相关 %d 条", len(items), len(topics))
        except requests.exceptions.RequestException as e:
            result["error"] = f"网络请求失败: {e}"
            logger.error("抖音热榜请求失败: %s", e)
        except Exception as e:
            result["error"] = f"解析失败: {e}"
            logger.error("抖音热榜解析失败: %s", e)
        return result

    def fetch_weibo(self) -> Dict[str, Any]:
        """抓取微博热搜。

        使用微博公开接口：https://weibo.com/ajax/side/hotSearch
        通过移动端 User-Agent 可获取完整热搜列表，无需登录。
        """
        result: Dict[str, Any] = {
            "platform": "weibo",
            "topics": [],
            "success": False,
            "error": None,
        }
        try:
            # 移动端 UA 可绕过登录限制
            headers = {
                "User-Agent": (
                    "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) "
                    "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1"
                ),
                "Referer": "https://weibo.com/",
            }
            resp = self.session.get(
                "https://weibo.com/ajax/side/hotSearch", headers=headers, timeout=15
            )
            resp.raise_for_status()
            data = resp.json()
            items = data.get("data", {}).get("realtime", [])
            topics = []
            for item in items:
                word = item.get("word", "")
                if any(k in word for k in self.keywords):
                    topics.append({
                        "rank": item.get("rank", item.get("realpos", "-")),
                        "topic": word,
                        "hot_value": item.get("raw_hot") or item.get("hot", 0),
                        "label": item.get("category", ""),
                    })
            result["topics"] = topics
            result["success"] = True
            logger.info("微博热搜抓取完成，共 %d 条，说唱相关 %d 条", len(items), len(topics))
        except requests.exceptions.RequestException as e:
            result["error"] = f"网络请求失败: {e}"
            logger.error("微博热搜请求失败: %s", e)
        except Exception as e:
            result["error"] = f"解析失败: {e}"
            logger.error("微博热搜解析失败: %s", e)
        return result


def fetch_hot_search(config: Dict[str, Any]) -> List[Dict[str, Any]]:
    """抓取微博和抖音热搜。"""
    cfg = config.get("hot_search", {})
    keywords = cfg.get("keywords", DEFAULT_RAP_KEYWORDS)
    fetcher = HotSearchFetcher(keywords)
    return [fetcher.fetch_douyin(), fetcher.fetch_weibo()]


def format_hot_search_for_report(results: List[Dict[str, Any]]) -> str:
    """将热搜结果格式化为 Markdown 文本。"""
    lines: List[str] = []
    lines.append("## 全网舆情与话题总览\n")
    has_content = False
    for r in results:
        platform_name = {"douyin": "抖音热榜", "weibo": "微博热搜"}.get(r["platform"], r["platform"])
        lines.append(f"### {platform_name}\n")
        if r.get("success") and r.get("topics"):
            has_content = True
            for topic in r["topics"][:10]:
                rank = topic.get("rank", "-")
                hot = topic.get("hot_value")
                hot_text = f"（热度 {hot}）" if hot else ""
                lines.append(f"- {rank}. {topic['topic']}{hot_text}")
        else:
            lines.append(f"- 暂无数据：{r.get('error', '未知原因')}")
        lines.append("")
    if not has_content:
        lines.append(
            "> 当前周期未抓取到说唱相关热搜，或平台接口需要额外配置。"
            "请人工补充舆情内容。"
        )
    return "\n".join(lines)
