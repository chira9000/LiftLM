"""Live PubMed search via the NCBI E-utilities API.

Supplements the curated KNOWLEDGE_BASE citations with fresh results at query
time. Best-effort like the Reddit provider: on any failure (network, rate
limit, malformed response) it returns an empty list rather than breaking the
coach flow. Results are cached in-memory per topic since PubMed's index for
an established topic doesn't meaningfully change within a process lifetime.
"""

from __future__ import annotations

import time

import httpx

from app.config import settings
from app.services.knowledge.library import PubMedCitation

_ESEARCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
_ESUMMARY_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"

# In-memory cache: query -> (cached_at, citations)
_search_cache: dict[str, tuple[float, list[PubMedCitation]]] = {}


class PubMedClient:
    """Search PubMed for citations relevant to a training-science query."""

    def __init__(self, result_limit: int | None = None):
        self.result_limit = result_limit if result_limit is not None else settings.pubmed_result_limit

    def _common_params(self) -> dict[str, str]:
        params = {"db": "pubmed", "retmode": "json", "tool": "liftai", "email": settings.pubmed_email}
        if settings.pubmed_api_key:
            params["api_key"] = settings.pubmed_api_key
        return params

    async def search(self, query: str) -> list[PubMedCitation]:
        query = (query or "").strip()
        if not query:
            return []

        cache_key = f"{query.lower()}::{self.result_limit}"
        cached = _search_cache.get(cache_key)
        if cached and time.time() < cached[0] + settings.pubmed_cache_ttl:
            return cached[1]

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                pmids = await self._esearch(client, query)
                if not pmids:
                    return []
                citations = await self._esummary(client, pmids)
        except (httpx.HTTPError, ValueError, KeyError):
            return []

        _search_cache[cache_key] = (time.time(), citations)
        return citations

    async def _esearch(self, client: httpx.AsyncClient, query: str) -> list[str]:
        resp = await client.get(
            _ESEARCH_URL,
            params={
                **self._common_params(),
                "term": query,
                "retmax": str(self.result_limit),
                "sort": "relevance",
            },
        )
        resp.raise_for_status()
        return resp.json().get("esearchresult", {}).get("idlist", [])

    async def _esummary(self, client: httpx.AsyncClient, pmids: list[str]) -> list[PubMedCitation]:
        resp = await client.get(
            _ESUMMARY_URL,
            params={**self._common_params(), "id": ",".join(pmids)},
        )
        resp.raise_for_status()
        result = resp.json().get("result", {})

        citations: list[PubMedCitation] = []
        for pmid in result.get("uids", []):
            doc = result.get(pmid) or {}
            title = (doc.get("title") or "").strip().rstrip(".")
            if not title:
                continue
            authors = doc.get("authors") or []
            first_author = authors[0]["name"] if authors else "Unknown"
            year = (doc.get("pubdate") or "").split(" ")[0].split("-")[0] or "n.d."
            suffix = " et al." if len(authors) > 1 else ""
            citations.append(
                PubMedCitation(pmid=pmid, citation=f"{first_author}{suffix} ({year}). {title}.")
            )
        return citations
