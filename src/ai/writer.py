"""AI 文案生成模块。

使用公司 AI 中转站（OpenAI 兼容接口）根据榜单数据生成：
- 各平台榜单一句话总结
- 头部艺人表现描述
- 跨平台爆款歌曲分析
- 周期性趋势观察

如果未配置 AI 或调用失败，会返回空字符串，不影响主流程。
"""
import logging
from typing import Any, Dict, List, Optional

import pandas as pd
from openai import OpenAI

logger = logging.getLogger("rap_report")


class AIWriter:
    """AI 文案生成器。"""

    def __init__(self, config: Dict[str, Any]) -> None:
        self.ai_config = config.get("ai", {})
        self.enabled = self.ai_config.get("enabled", False)
        self.base_url = self.ai_config.get("base_url", "")
        self.api_key = self.ai_config.get("api_key", "")
        self.model = self.ai_config.get("model", "gpt-4o-mini")
        self.max_tokens = self.ai_config.get("max_tokens", 2000)
        self.temperature = self.ai_config.get("temperature", 0.7)

        self.client: Optional[OpenAI] = None
        if self.enabled and self.base_url and self.api_key:
            try:
                self.client = OpenAI(base_url=self.base_url, api_key=self.api_key)
            except Exception as e:
                logger.error("AI 客户端初始化失败: %s", e)
                self.enabled = False

    def _call(self, prompt: str) -> str:
        """调用 AI 接口。"""
        if not self.enabled or not self.client:
            logger.info("AI 未启用或未配置，跳过文案生成")
            return ""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "你是一位说唱音乐行业分析师，擅长根据榜单数据撰写简洁、专业的双周报文案。输出使用中文，不要编造数据。"},
                    {"role": "user", "content": prompt},
                ],
                max_tokens=self.max_tokens,
                temperature=self.temperature,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error("AI 调用失败: %s", e)
            return ""

    def generate_platform_summary(self, analysis: Dict[str, Any]) -> str:
        """生成各平台榜单总结。"""
        df = analysis.get("raw", pd.DataFrame())
        if df.empty:
            return ""

        platform_texts = []
        for platform, group in df.groupby("platform"):
            top3 = group.nsmallest(3, "rank")[["rank", "song_name", "artist"]]
            top3_text = "\n".join(
                [f"{row['rank']}. {row['song_name']} - {row['artist']}" for _, row in top3.iterrows()]
            )
            platform_texts.append(f"平台：{platform}\nTOP3：\n{top3_text}")

        prompt = (
            "根据以下说唱音乐榜单数据，为每个平台生成一段 50-100 字的简短总结，"
            "说明该平台本期榜单的主要特征（头部歌曲、艺人集中程度、新歌表现等）：\n\n"
            + "\n\n".join(platform_texts)
        )
        return self._call(prompt)

    def generate_artist_insight(self, artist_summary: pd.DataFrame) -> str:
        """生成头部艺人表现描述。"""
        if artist_summary.empty:
            return ""
        top10 = artist_summary.head(10)[["artist", "total_entries", "platform_count", "best_rank"]]
        text = top10.to_string(index=False)
        prompt = (
            "根据以下头部艺人跨平台上榜数据，生成一段 100-150 字的分析，"
            "指出本期表现最突出的艺人、跨平台覆盖情况以及平台偏好：\n\n"
            + text
        )
        return self._call(prompt)

    def generate_hit_songs_insight(self, hits_df: pd.DataFrame) -> str:
        """生成跨平台爆款歌曲分析。"""
        if hits_df.empty:
            return ""
        text = hits_df[["song_name", "artist", "platform_count", "best_rank"]].to_string(index=False)
        prompt = (
            "根据以下跨平台爆款歌曲数据（在多个平台同时上榜），"
            "生成一段 80-120 字的分析，说明哪些歌曲实现了跨平台破圈以及可能的原因：\n\n"
            + text
        )
        return self._call(prompt)

    def generate_all(self, analysis: Dict[str, Any]) -> Dict[str, str]:
        """生成所有 AI 文案。"""
        return {
            "platform_summary": self.generate_platform_summary(analysis),
            "artist_insight": self.generate_artist_insight(analysis["artist_summary"]),
            "hit_songs_insight": self.generate_hit_songs_insight(analysis["cross_platform_hits"]),
        }
