"""数据清洗工具。

统一歌曲名、艺人名格式，减少跨平台匹配时的噪声：
- 去除首尾空格
- 统一中英文括号
- 标准化 feat./with/and 等合作标识
- 去除部分版本后缀（如 Explicit, Album Version）
- 统一大小写（艺名首字母大写）
"""
import re
import unicodedata


def normalize_text(text: str) -> str:
    """基础文本清洗：去空格、统一标点。"""
    if not isinstance(text, str):
        text = str(text)
    # 去除首尾空格，压缩连续空格
    text = re.sub(r"\s+", " ", text.strip())
    # 统一全角空格
    text = text.replace("　", " ")
    return text


def normalize_song_name(name: str) -> str:
    """标准化歌曲名。

    保留核心歌名，去除常见版本标注但保留 (Live) 等表演标识。
    """
    name = normalize_text(name)
    # 统一中英文括号为英文半角
    name = name.replace("（", "(").replace("）", ")")
    # 去除 Explicit/Edited/Album Version/Remix 等版本后缀
    name = re.sub(r"\s*\(Explicit\)", "", name, flags=re.IGNORECASE)
    name = re.sub(r"\s*\(Edited\)", "", name, flags=re.IGNORECASE)
    name = re.sub(r"\s*\(Album Version[^)]*\)", "", name, flags=re.IGNORECASE)
    name = re.sub(r"\s*\(feat\.[^)]*\)", "", name, flags=re.IGNORECASE)
    name = re.sub(r"\s*\(with [^)]*\)", "", name, flags=re.IGNORECASE)
    # 去除中英混用的多余空格，如 "周旋 " -> "周旋"
    name = re.sub(r"\s+", " ", name).strip()
    return name


def normalize_artist(artist: str) -> str:
    """标准化艺人名。

    统一分隔符、去除多余空格、统一大小写格式。
    """
    artist = normalize_text(artist)
    # 统一中英文逗号、顿号为 '/'
    artist = artist.replace("、", "/").replace(",", "/")
    # 去除括号内内容（通常是 feat. 信息已在歌曲名处理）
    artist = re.sub(r"\s*\([^)]*\)", "", artist)
    # 分割多个艺人并分别清洗
    parts = [p.strip() for p in artist.split("/") if p.strip()]
    cleaned = []
    for part in parts:
        # 去除前后空格，保留原始大小写但去除多余空格
        part = re.sub(r"\s+", " ", part).strip()
        if part:
            cleaned.append(part)
    return "/".join(cleaned)


def normalize_for_matching(name: str) -> str:
    """用于跨平台匹配的最终键：小写、去除所有标点和空格。"""
    name = normalize_text(name)
    name = name.lower()
    # 去除括号及内容
    name = re.sub(r"[（(].*?[）)]", "", name)
    # 去除标点符号和空格
    name = re.sub(r"[^\w一-鿿]", "", name)
    # 去除常见虚词
    for word in ["live", "explicit", "edited", "albumversion", "remix"]:
        name = name.replace(word, "")
    return name


def build_match_key(song_name: str, artist: str) -> str:
    """构建跨平台匹配键。"""
    return f"{normalize_for_matching(song_name)}::{normalize_for_matching(artist)}"
