# utils/text_utils.py
import re


def clean_title(title: str, max_len: int = 40) -> str:
    title = title.replace("_", " ").strip()
    title = re.sub(r'\s+', ' ', title)
    title = title.title()
    if len(title) > max_len:
        title = title[:max_len - 3] + "..."
    return title or "Node"


def truncate(text: str, max_len: int = 200) -> str:
    return text[:max_len] + "..." if len(text) > max_len else text
