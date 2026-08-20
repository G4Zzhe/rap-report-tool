"""公共工具：配置加载、日志、统一请求。"""
import os
import logging
from pathlib import Path
from typing import Dict, Any

import yaml

# 项目根目录
ROOT_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = ROOT_DIR / "output"
OUTPUT_DIR.mkdir(exist_ok=True)


def load_config() -> Dict[str, Any]:
    """加载 config.yaml 与 config.local.yaml（后者覆盖前者）。"""
    config: Dict[str, Any] = {}
    config_path = ROOT_DIR / "config.yaml"
    local_config_path = ROOT_DIR / "config.local.yaml"

    if config_path.exists():
        with open(config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f) or {}

    if local_config_path.exists():
        with open(local_config_path, "r", encoding="utf-8") as f:
            local_config = yaml.safe_load(f) or {}
        _deep_update(config, local_config)

    # 允许通过环境变量覆盖 AI 配置（GitHub Actions 用）
    ai = config.setdefault("ai", {})
    ai["base_url"] = os.getenv("AI_BASE_URL", ai.get("base_url", ""))
    ai["api_key"] = os.getenv("AI_API_KEY", ai.get("api_key", ""))
    ai["model"] = os.getenv("AI_MODEL", ai.get("model", "gpt-4o-mini"))

    return config


def _deep_update(base: Dict[str, Any], update: Dict[str, Any]) -> None:
    """递归更新字典。"""
    for key, value in update.items():
        if isinstance(value, dict) and key in base and isinstance(base[key], dict):
            _deep_update(base[key], value)
        else:
            base[key] = value


def setup_logging() -> logging.Logger:
    """配置日志。"""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    return logging.getLogger("rap_report")


def get_headers() -> Dict[str, str]:
    """返回常用请求头，降低被反爬概率。"""
    return {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/126.0.0.0 Safari/537.36"
        ),
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
    }
