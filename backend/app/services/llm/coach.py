"""LLM service with pluggable providers (mock, ollama, mlx, openai)."""

import asyncio
import json
from abc import ABC, abstractmethod

import httpx

from app.config import settings
from app.services.llm.muscle_groups import detect_muscle_groups
from app.services.social import gather_community_insights


SYSTEM_PROMPT = """You are LiftAI, an expert strength training coach. You help lifters understand their training data and make smart decisions.

You receive structured analytics about the user's training — NOT raw workout logs. Use this data to give specific, actionable advice.

You may also receive COMMUNITY INSIGHTS scraped from Reddit (lifting subreddits). Treat these as anecdotal community experience — useful for ideas and common patterns, but secondary to the user's own analytics. Cite Reddit only when it adds value (e.g. "lifters on r/weightroom often…") and never invent posts that aren't in the context.

Guidelines:
- Be concise but thorough (2-4 paragraphs max)
- Reference specific numbers from the analytics when relevant
- For "what should I do today" questions, give concrete sets/reps/weight recommendations
- Explain plateaus with evidence from trends, RPE, frequency, and volume
- Never invent data not present in the context
- If data is insufficient, say so and suggest what to track
- When community insights are present, briefly weave in 1–2 relevant takeaways and mention the subreddit
- If the context includes a MUSCLE GROUP FOCUS block, the user asked about a specific muscle group (chest, back, legs, shoulders, arms, or core) — explicitly name that muscle group in your answer and lead with the exercises listed there, even if the user didn't name a specific exercise"""


class LLMProvider(ABC):
    @abstractmethod
    async def generate(self, messages: list[dict], context: dict) -> str:
        pass


def _format_community_block(context: dict) -> str:
    insights = context.get("community_insights") or []
    if not insights:
        return ""
    lines = ["\n\n--- COMMUNITY INSIGHTS (Reddit) ---"]
    for i, item in enumerate(insights, 1):
        sub = f"r/{item['subreddit']}" if item.get("subreddit") else "Reddit"
        lines.append(
            f"{i}. [{sub}] {item.get('title', '')} "
            f"(score {item.get('score', 0)}, {item.get('num_comments', 0)} comments)\n"
            f"   {item.get('snippet') or '(no body)'}\n"
            f"   URL: {item.get('url', '')}"
        )
    lines.append("--- END COMMUNITY INSIGHTS ---")
    return "\n".join(lines)


def _format_muscle_focus_block(context: dict) -> str:
    focus = context.get("muscle_group_focus")
    if not focus:
        return ""
    groups = ", ".join(focus["detected_muscle_groups"])
    matches = focus["matching_exercises"]
    lines = [f"\n\n--- MUSCLE GROUP FOCUS: {groups} ---"]
    if matches:
        lines.append(json.dumps(matches, indent=2))
    else:
        lines.append(f"(no logged exercises tagged with muscle group: {groups})")
    lines.append("--- END MUSCLE GROUP FOCUS ---")
    return "\n".join(lines)


def _build_full_messages(messages: list[dict], context: dict) -> list[dict]:
    skip_keys = {"community_insights", "muscle_group_focus"}
    context_block = (
        f"\n\n--- TRAINING ANALYTICS ---\n"
        f"{json.dumps({k: v for k, v in context.items() if k not in skip_keys}, indent=2)}\n"
        f"--- END ANALYTICS ---"
        + _format_muscle_focus_block(context)
        + _format_community_block(context)
    )
    full_messages = [{"role": "system", "content": SYSTEM_PROMPT + context_block}]
    full_messages.extend(messages)
    return full_messages


def _auth_headers() -> dict[str, str]:
    if settings.llm_api_key:
        return {"Authorization": f"Bearer {settings.llm_api_key}"}
    return {}


class MockLLMProvider(LLMProvider):
    """Rule-based responses for development without a local model."""

    async def generate(self, messages: list[dict], context: dict) -> str:
        user_msg = messages[-1]["content"].lower()
        exercises = context.get("exercises", [])
        summary = context.get("summary", {})
        community = context.get("community_insights") or []

        def with_community(base: str) -> str:
            if not community:
                return base
            lines = ["\n\n**From Reddit**"]
            for item in community[:3]:
                sub = f"r/{item['subreddit']}" if item.get("subreddit") else "Reddit"
                lines.append(f"• [{sub}] {item['title']}")
                if item.get("snippet"):
                    lines.append(f"  _{item['snippet'][:180]}{'…' if len(item.get('snippet', '')) > 180 else ''}_")
            return base + "\n".join(lines)

        muscle_focus = context.get("muscle_group_focus")
        if muscle_focus:
            groups = "/".join(muscle_focus["detected_muscle_groups"])
            matches = muscle_focus["matching_exercises"]
            if matches:
                lines = [f"**{groups.title()} Exercises**\n"]
                for e in matches:
                    trend = e.get("trend_last_4", [])
                    trend_str = " → ".join(f"{t['e1rm']} lbs e1RM" for t in trend) if trend else "insufficient data"
                    lines.append(
                        f"• **{e['name']}** — e1RM {e['estimated_1rm']} lbs "
                        f"(PR {e['pr_weight']}×{e['pr_reps']}), {e['frequency_per_week']:.1f}x/week, "
                        f"last performed {e.get('last_performed', 'unknown')}. Trend: {trend_str}."
                    )
                return with_community("\n".join(lines))
            article = "an" if groups[0] in "aeiou" else "a"
            return with_community(
                f"You don't have any logged **{groups}** exercises yet. "
                f"Log {article} {groups} workout and I'll be able to analyze it."
            )

        if "bench" in user_msg:
            bench = next((e for e in exercises if "bench" in e["name"].lower()), None)
            if bench:
                trend = bench.get("trend_last_4", [])
                trend_str = " → ".join(f"{t['e1rm']} lbs e1RM" for t in trend) if trend else "insufficient data"
                return with_community(
                    f"**Bench Press Analysis**\n\n"
                    f"Your estimated 1RM is **{bench['estimated_1rm']} lbs** "
                    f"(PR: {bench['pr_weight']}×{bench['pr_reps']}). "
                    f"You've trained bench **{bench['total_sessions']} sessions** "
                    f"at **{bench['frequency_per_week']:.1f}x/week**.\n\n"
                    f"Recent e1RM trend: {trend_str}.\n\n"
                    f"{'Avg RPE: ' + str(bench['avg_rpe']) + ' — intensity looks appropriate.' if bench.get('avg_rpe') else 'Start logging RPE for better recommendations.'}"
                )

        if "squat" in user_msg and ("stop" in user_msg or "plateau" in user_msg or "stuck" in user_msg):
            squat = next((e for e in exercises if "squat" in e["name"].lower()), None)
            if squat:
                trend = squat.get("trend_last_4", [])
                issues = []
                if squat["frequency_per_week"] < 1.5:
                    issues.append(f"Low frequency ({squat['frequency_per_week']:.1f}x/week) — aim for 2x/week minimum")
                if squat.get("avg_rpe") and squat["avg_rpe"] > 9:
                    issues.append(f"High average RPE ({squat['avg_rpe']}) — you may be training too close to failure")
                if len(trend) >= 2 and trend[-1]["e1rm"] <= trend[0]["e1rm"]:
                    issues.append("e1RM has flatlined over recent sessions")
                if not issues:
                    issues.append("Volume or recovery may be limiting — check sleep, nutrition, and weekly volume trends")

                return with_community(
                    f"**Squat Plateau Analysis**\n\n"
                    f"Current e1RM: **{squat['estimated_1rm']} lbs**. "
                    f"Last performed: {squat.get('last_performed', 'unknown')}.\n\n"
                    f"Likely factors:\n" + "\n".join(f"• {i}" for i in issues)
                )

        if "today" in user_msg or "should i do" in user_msg:
            if exercises:
                top = exercises[0]
                return with_community(
                    f"**Today's Recommendation**\n\n"
                    f"Based on your data, focus on **{top['name']}**:\n"
                    f"• Work up to {top['pr_weight']} lbs × {max(top['pr_reps'] - 1, 5)} reps for 3-4 working sets\n"
                    f"• Target RPE 7-8 on working sets\n"
                    f"• You've logged {summary.get('workouts_this_week', 0)} workouts this week "
                    f"({summary.get('volume_this_week', 0):,.0f} lbs total volume)\n\n"
                    f"Check the Progression tab for exercise-specific weight recommendations."
                )

        return with_community(
            f"**Training Overview**\n\n"
            f"You've completed **{summary.get('total_workouts', 0)} workouts** "
            f"with **{summary.get('total_volume', 0):,.0f} lbs** total volume.\n\n"
            f"Top lifts: {', '.join(e['name'] + ' (' + str(e['estimated_1rm']) + ' lbs e1RM)' for e in exercises[:3])}.\n\n"
            f"Ask me about specific exercises, today's workout, or why progress has stalled."
        )


class OllamaLLMProvider(LLMProvider):
    """Local Qwen via Ollama (recommended for Qwen3-32B on a GPU workstation)."""

    async def generate(self, messages: list[dict], context: dict) -> str:
        full_messages = _build_full_messages(messages, context)
        payload: dict = {
            "model": settings.llm_model,
            "messages": full_messages,
            "stream": False,
            "think": settings.llm_think,
            "options": {
                "temperature": settings.llm_temperature,
                "num_predict": settings.llm_max_tokens,
            },
        }

        async with httpx.AsyncClient(timeout=settings.llm_timeout) as client:
            resp = await client.post(
                f"{settings.llm_base_url.rstrip('/')}/api/chat",
                json=payload,
            )
            resp.raise_for_status()
            return resp.json()["message"]["content"]


class OpenAICompatibleLLMProvider(LLMProvider):
    """vLLM, SGLang, or any OpenAI-compatible inference server."""

    async def generate(self, messages: list[dict], context: dict) -> str:
        full_messages = _build_full_messages(messages, context)
        base = settings.llm_base_url.rstrip("/")
        url = base if base.endswith("/chat/completions") else f"{base}/chat/completions"

        async with httpx.AsyncClient(timeout=settings.llm_timeout) as client:
            resp = await client.post(
                url,
                headers=_auth_headers(),
                json={
                    "model": settings.llm_model,
                    "messages": full_messages,
                    "temperature": settings.llm_temperature,
                    "max_tokens": settings.llm_max_tokens,
                },
            )
            resp.raise_for_status()
            return resp.json()["choices"][0]["message"]["content"]


_mlx_model_cache: dict[str, tuple] = {}


def _load_mlx_model():
    from mlx_lm import load  # type: ignore

    model_id = settings.llm_model
    if model_id not in _mlx_model_cache:
        _mlx_model_cache[model_id] = load(model_id)
    return _mlx_model_cache[model_id]


def _mlx_generate_sync(full_messages: list[dict]) -> str:
    from mlx_lm import generate  # type: ignore
    from mlx_lm.sample_utils import make_sampler  # type: ignore

    model, tokenizer = _load_mlx_model()
    if hasattr(tokenizer, "apply_chat_template"):
        prompt = tokenizer.apply_chat_template(
            full_messages,
            tokenize=False,
            add_generation_prompt=True,
        )
    else:
        prompt = "\n".join(f"{m['role']}: {m['content']}" for m in full_messages) + "\nassistant:"

    sampler = make_sampler(temp=settings.llm_temperature)
    return generate(
        model,
        tokenizer,
        prompt=prompt,
        max_tokens=settings.llm_max_tokens,
        sampler=sampler,
        verbose=False,
    )


class MLXLLMProvider(LLMProvider):
    """MLX-native inference on Apple Silicon (~1–3 GB quantized models)."""

    async def generate(self, messages: list[dict], context: dict) -> str:
        try:
            full_messages = _build_full_messages(messages, context)
            return await asyncio.to_thread(_mlx_generate_sync, full_messages)
        except ImportError:
            fallback = MockLLMProvider()
            return await fallback.generate(messages, context)


def get_llm_provider() -> LLMProvider:
    providers = {
        "mock": MockLLMProvider,
        "ollama": OllamaLLMProvider,
        "openai": OpenAICompatibleLLMProvider,
        "mlx": MLXLLMProvider,
    }
    cls = providers.get(settings.llm_provider, MockLLMProvider)
    return cls()


class CoachService:
    def __init__(self):
        self.provider = get_llm_provider()

    async def chat(self, message: str, history: list[dict], context: dict) -> tuple[str, list[dict]]:
        insights = await gather_community_insights(message)
        sources = [i.to_dict() for i in insights]
        enriched = {**context, "community_insights": sources}

        detected_groups = detect_muscle_groups(message)
        if detected_groups:
            exercises = context.get("exercises", [])
            matches = [e for e in exercises if (e.get("muscle_group") or "").lower() in detected_groups]
            enriched["muscle_group_focus"] = {
                "detected_muscle_groups": detected_groups,
                "matching_exercises": matches,
            }

        messages = [{"role": m["role"], "content": m["content"]} for m in history]
        messages.append({"role": "user", "content": message})
        reply = await self.provider.generate(messages, enriched)
        return reply, sources
