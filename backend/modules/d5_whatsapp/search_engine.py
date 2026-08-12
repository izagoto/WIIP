from __future__ import annotations


def build_snippet(content: str, query: str, *, radius: int = 60) -> str:
    text = (content or "").replace("\n", " ").strip()
    if not text:
        return ""

    needle = (query or "").strip()
    if not needle:
        return text[: radius * 2]

    lower = text.lower()
    idx = lower.find(needle.lower())
    if idx < 0:
        return text[: radius * 2] + ("…" if len(text) > radius * 2 else "")

    start = max(0, idx - radius)
    end = min(len(text), idx + len(needle) + radius)
    snippet = text[start:end]
    if start > 0:
        snippet = "…" + snippet
    if end < len(text):
        snippet = snippet + "…"
    return snippet
