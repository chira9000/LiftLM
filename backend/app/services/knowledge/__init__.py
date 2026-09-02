"""Training-science knowledge base: curated topics + live PubMed citations."""

from app.services.knowledge.library import KNOWLEDGE_BASE, KnowledgeEntry, PubMedCitation
from app.services.knowledge.pubmed import PubMedClient
from app.services.knowledge.retrieval import match_topics

__all__ = [
    "KNOWLEDGE_BASE",
    "KnowledgeEntry",
    "PubMedCitation",
    "PubMedClient",
    "match_topics",
    "gather_knowledge_context",
]


async def gather_knowledge_context(query: str) -> dict | None:
    """Match `query` against the knowledge base and enrich with live PubMed citations.

    Returns None when knowledge lookup is disabled or nothing matched, so
    callers can skip adding an empty block to the LLM context.
    """
    from app.config import settings

    if not settings.knowledge_enabled:
        return None

    entries = match_topics(query, limit=settings.knowledge_result_limit)
    if not entries:
        return None

    entry_dicts = [e.to_dict() for e in entries]

    if settings.pubmed_enabled:
        client = PubMedClient()
        for entry, entry_dict in zip(entries, entry_dicts):
            if not entry.pubmed_query:
                continue
            existing_pmids = {c["pmid"] for c in entry_dict["citations"]}
            live_citations = await client.search(entry.pubmed_query)
            for citation in live_citations:
                if citation.pmid not in existing_pmids:
                    entry_dict["citations"].append(citation.to_dict())
                    existing_pmids.add(citation.pmid)

    return {"entries": entry_dicts}
