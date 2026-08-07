import re

WHITESPACE_PATTERN = re.compile(r"\s+")


def normalize_text(text: str) -> str:
    return WHITESPACE_PATTERN.sub(" ", text).strip()
