"""Keyword-based knowledge base retrieval.

Same deterministic approach as intent.py / muscle_groups.py: no training
data or embeddings yet, so match the message against each entry's keyword
list and rank by number of distinct keyword hits.
"""

import re

from app.services.knowledge.library import KNOWLEDGE_BASE, KnowledgeEntry

_WORD_BOUNDARY_CACHE: dict[str, re.Pattern] = {}


def _keyword_pattern(keyword: str) -> re.Pattern:
    pattern = _WORD_BOUNDARY_CACHE.get(keyword)
    if pattern is None:
        pattern = re.compile(rf"\b{re.escape(keyword)}\b", re.IGNORECASE)
        _WORD_BOUNDARY_CACHE[keyword] = pattern
    return pattern


def match_topics(text: str, limit: int | None = None) -> list[KnowledgeEntry]:
    """Return knowledge base entries relevant to `text`, ranked by keyword-hit count."""
    scored: list[tuple[int, KnowledgeEntry]] = []
    for entry in KNOWLEDGE_BASE:
        hits = sum(1 for kw in entry.keywords if _keyword_pattern(kw).search(text))
        if hits:
            scored.append((hits, entry))

    scored.sort(key=lambda pair: pair[0], reverse=True)
    entries = [entry for _, entry in scored]
    return entries[:limit] if limit is not None else entries
