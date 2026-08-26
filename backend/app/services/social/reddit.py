"""Reddit search for strength-training community answers.

Uses the official Reddit OAuth API when credentials are set
(REDDIT_CLIENT_ID / REDDIT_CLIENT_SECRET). Falls back to the public
JSON search endpoint when credentials are absent (may be rate-limited
or blocked depending on network).

Structured so additional social providers can plug in later.
"""

from __future__ import annotations

import time
from dataclasses import asdict, dataclass

import httpx

from app.config import settings

# In-memory OAuth token cache (process-local)
_token_cache: dict[str, float | str] = {"access_token": "", "expires_at": 0.0}


@dataclass
class SocialInsight:
    platform: str
    title: str
    url: str
    snippet: str
    score: int
    subreddit: str | None = None
    num_comments: int = 0

    def to_dict(self) -> dict:
        return asdict(self)


class RedditResearchProvider:
    """Search Reddit for posts relevant to a training question."""

    def __init__(
        self,
        subreddits: list[str] | None = None,
        limit: int | None = None,
        user_agent: str | None = None,
    ):
        self.subreddits = subreddits or settings.reddit_subreddits
        self.limit = limit if limit is not None else settings.reddit_result_limit
        self.user_agent = user_agent or settings.reddit_user_agent

    async def research(self, query: str) -> list[SocialInsight]:
        query = (query or "").strip()
        if not query:
            return []

        async with httpx.AsyncClient(timeout=25.0, follow_redirects=True) as client:
            if settings.reddit_client_id and settings.reddit_client_secret:
                posts = await self._oauth_search(client, query)
            else:
                posts = await self._public_search(client, query)

        return self._posts_to_insights(posts)

    async def _get_oauth_token(self, client: httpx.AsyncClient) -> str | None:
        now = time.time()
        cached = str(_token_cache.get("access_token") or "")
        expires_at = float(_token_cache.get("expires_at") or 0)
        if cached and now < expires_at - 60:
            return cached

        try:
            resp = await client.post(
                "https://www.reddit.com/api/v1/access_token",
                data={"grant_type": "client_credentials"},
                auth=(settings.reddit_client_id, settings.reddit_client_secret),
                headers={"User-Agent": self.user_agent},
            )
            resp.raise_for_status()
            payload = resp.json()
            token = payload.get("access_token")
            if not token:
                return None
            _token_cache["access_token"] = token
            _token_cache["expires_at"] = now + float(payload.get("expires_in", 3600))
            return token
        except (httpx.HTTPError, ValueError, KeyError):
            return None

    async def _oauth_search(self, client: httpx.AsyncClient, query: str) -> list[dict]:
        token = await self._get_oauth_token(client)
        if not token:
            return await self._public_search(client, query)

        sub_path = "+".join(self.subreddits)
        url = f"https://oauth.reddit.com/r/{sub_path}/search"
        params = {
            "q": query,
            "restrict_sr": "true",
            "sort": "relevance",
            "t": "year",
            "limit": str(self.limit),
            "type": "link",
            "raw_json": "1",
        }
        headers = {
            "User-Agent": self.user_agent,
            "Authorization": f"Bearer {token}",
        }
        try:
            resp = await client.get(url, params=params, headers=headers)
            resp.raise_for_status()
            data = resp.json()
            return [c.get("data") or {} for c in data.get("data", {}).get("children", [])]
        except (httpx.HTTPError, ValueError, KeyError):
            return []

    async def _public_search(self, client: httpx.AsyncClient, query: str) -> list[dict]:
        """Unauthenticated JSON search — often blocked; best-effort fallback."""
        sub_path = "+".join(self.subreddits)
        url = f"https://www.reddit.com/r/{sub_path}/search.json"
        params = {
            "q": query,
            "restrict_sr": "true",
            "sort": "relevance",
            "t": "year",
            "limit": str(self.limit),
            "type": "link",
            "raw_json": "1",
        }
        headers = {
            "User-Agent": self.user_agent,
            "Accept": "application/json",
        }
        try:
            resp = await client.get(url, params=params, headers=headers)
            if resp.status_code != 200:
                return []
            data = resp.json()
            return [c.get("data") or {} for c in data.get("data", {}).get("children", [])]
        except (httpx.HTTPError, ValueError, KeyError):
            return []

    def _posts_to_insights(self, posts: list[dict]) -> list[SocialInsight]:
        insights: list[SocialInsight] = []
        for post in posts:
            if post.get("over_18"):
                continue
            title = (post.get("title") or "").strip()
            if not title:
                continue

            selftext = (post.get("selftext") or "").strip().replace("\n", " ")
            snippet = selftext[:400] if selftext else (post.get("link_flair_text") or "")
            permalink = post.get("permalink") or ""
            post_url = f"https://www.reddit.com{permalink}" if permalink else (post.get("url") or "")

            insights.append(
                SocialInsight(
                    platform="reddit",
                    title=title,
                    url=post_url,
                    snippet=snippet,
                    score=int(post.get("score") or 0),
                    subreddit=post.get("subreddit"),
                    num_comments=int(post.get("num_comments") or 0),
                )
            )

        insights.sort(key=lambda i: (i.score, i.num_comments), reverse=True)
        return insights[: self.limit]
