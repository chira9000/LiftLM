"""Community research providers (Reddit now; more platforms later)."""

from app.services.social.reddit import RedditResearchProvider, SocialInsight

__all__ = ["RedditResearchProvider", "SocialInsight", "gather_community_insights"]


async def gather_community_insights(query: str) -> list[SocialInsight]:
    """Aggregate insights from enabled social providers."""
    from app.config import settings

    insights: list[SocialInsight] = []
    if settings.reddit_enabled:
        provider = RedditResearchProvider()
        insights.extend(await provider.research(query))
    return insights
