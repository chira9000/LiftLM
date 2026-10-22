"""LLM service with pluggable providers (mock, ollama, mlx, openai)."""

import asyncio
import json
from abc import ABC, abstractmethod

import httpx

from app.config import settings
from app.services.knowledge import gather_knowledge_context
from app.services.llm.intent import extract_query_intent
from app.services.llm.intent_classifier import classify_intent
from app.services.llm.muscle_groups import detect_muscle_groups, parent_muscle_group
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
- If the context includes a MUSCLE GROUP FOCUS block, the user asked about a specific muscle group (chest, back, legs, shoulders, arms, or core) — explicitly name that muscle group in your answer and lead with the exercises listed there, even if the user didn't name a specific exercise
- If the context includes a QUERY INTENT block, it's a structured extraction of the user's message (exercise, problem, weight, reps, goal, timeframe, experience_level — any field may be null). Treat non-null fields as confirmed facts about what the user is asking; don't ask them to repeat information already present there. If "problem" is "plateau", address it as a plateau using the exercise's trend/RPE/frequency data. If "goal" or "experience_level" is set, tailor the recommendation to it
- If the context includes an INTENT CLASSIFICATION block, "intent" is the classified category of the message (PROGRAMMING, EXERCISE_SELECTION, TECHNIQUE, PROGRESSION, PLATEAU, RECOVERY, NUTRITION, EQUIPMENT, WORKOUT_ANALYSIS, GENERAL, or UNKNOWN), with optional "body_part" and "goal". Let it set the shape of your answer — e.g. PLATEAU walks through trend/RPE/frequency evidence, RECOVERY addresses rest/sleep/deload, NUTRITION gives dietary guidance, EQUIPMENT suggests substitutions, TECHNIQUE focuses on form cues, PROGRAMMING/EXERCISE_SELECTION focus on structuring or picking exercises
- If the context includes a KNOWLEDGE BASE block, it contains curated training-science summaries (progressive overload, volume, RPE/RIR, recovery, programming, deloading, technique, plateaus, strength standards, nutrition, etc.) with real supporting PubMed citations. Use it to ground advice in evidence and weave in a citation inline (e.g. "per Schoenfeld et al., PMID 27433992") when it directly supports a claim you're making. Never cite a PubMed source, PMID, or study that isn't present in that block"""


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


def _format_query_intent_block(context: dict) -> str:
    intent = context.get("query_intent")
    if not intent:
        return ""
    return (
        f"\n\n--- QUERY INTENT ---\n"
        f"{json.dumps(intent, indent=2)}\n"
        f"--- END QUERY INTENT ---"
    )


def _format_intent_classification_block(context: dict) -> str:
    classification = context.get("intent_classification")
    if not classification:
        return ""
    return (
        f"\n\n--- INTENT CLASSIFICATION ---\n"
        f"{json.dumps(classification, indent=2)}\n"
        f"--- END INTENT CLASSIFICATION ---"
    )


def _format_knowledge_block(context: dict) -> str:
    knowledge = context.get("knowledge_base")
    entries = knowledge.get("entries") if knowledge else None
    if not entries:
        return ""
    lines = ["\n\n--- KNOWLEDGE BASE (curated + PubMed) ---"]
    for entry in entries:
        lines.append(f"\n[{entry['title']}]")
        lines.append(entry["summary"])
        for point in entry["key_points"]:
            lines.append(f"  • {point}")
        if entry["citations"]:
            lines.append("  Sources:")
            for c in entry["citations"]:
                lines.append(f"    - {c['citation']} (PMID:{c['pmid']}, {c['url']})")
    lines.append("--- END KNOWLEDGE BASE ---")
    return "\n".join(lines)


def _build_full_messages(messages: list[dict], context: dict) -> list[dict]:
    skip_keys = {
        "community_insights", "muscle_group_focus", "query_intent",
        "intent_classification", "knowledge_base",
    }
    context_block = (
        f"\n\n--- TRAINING ANALYTICS ---\n"
        f"{json.dumps({k: v for k, v in context.items() if k not in skip_keys}, indent=2)}\n"
        f"--- END ANALYTICS ---"
        + _format_muscle_focus_block(context)
        + _format_query_intent_block(context)
        + _format_intent_classification_block(context)
        + _format_knowledge_block(context)
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
        knowledge_entries = (context.get("knowledge_base") or {}).get("entries") or []

        def with_knowledge(base: str) -> str:
            if not knowledge_entries:
                return base
            lines = ["\n\n**Research context**"]
            for entry in knowledge_entries:
                lines.append(f"• **{entry['title']}** — {entry['summary']}")
                for c in entry["citations"][:2]:
                    lines.append(f"  _{c['citation']}_ (PMID:{c['pmid']})")
            return base + "\n".join(lines)

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

        def with_context(base: str) -> str:
            return with_community(with_knowledge(base))

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
                return with_context("\n".join(lines))
            article = "an" if groups[0] in "aeiou" else "a"
            return with_context(
                f"You don't have any logged **{groups}** exercises yet. "
                f"Log {article} {groups} workout and I'll be able to analyze it."
            )

        intent = context.get("query_intent")
        if intent and intent.get("problem") == "plateau":
            target_name = intent.get("exercise")
            lift = next((e for e in exercises if e["name"] == target_name), None) if target_name else None
            if lift:
                trend = lift.get("trend_last_4", [])
                issues = []
                if lift["frequency_per_week"] < 1.5:
                    issues.append(f"Low frequency ({lift['frequency_per_week']:.1f}x/week) — aim for 2x/week minimum")
                if lift.get("avg_rpe") and lift["avg_rpe"] > 9:
                    issues.append(f"High average RPE ({lift['avg_rpe']}) — you may be training too close to failure")
                if len(trend) >= 2 and trend[-1]["e1rm"] <= trend[0]["e1rm"]:
                    issues.append("e1RM has flatlined over recent sessions")
                if not issues:
                    issues.append("Volume or recovery may be limiting — check sleep, nutrition, and weekly volume trends")

                goal_line = f"\n\nGoal: **{intent['goal']}**." if intent.get("goal") else ""
                return with_context(
                    f"**{lift['name']} Plateau Analysis**\n\n"
                    f"Current e1RM: **{lift['estimated_1rm']} lbs**. "
                    f"Last performed: {lift.get('last_performed', 'unknown')}.{goal_line}\n\n"
                    f"Likely factors:\n" + "\n".join(f"• {i}" for i in issues)
                )

        if "bench" in user_msg:
            bench = next((e for e in exercises if "bench" in e["name"].lower()), None)
            if bench:
                trend = bench.get("trend_last_4", [])
                trend_str = " → ".join(f"{t['e1rm']} lbs e1RM" for t in trend) if trend else "insufficient data"
                return with_context(
                    f"**Bench Press Analysis**\n\n"
                    f"Your estimated 1RM is **{bench['estimated_1rm']} lbs** "
                    f"(PR: {bench['pr_weight']}×{bench['pr_reps']}). "
                    f"You've trained bench **{bench['total_sessions']} sessions** "
                    f"at **{bench['frequency_per_week']:.1f}x/week**.\n\n"
                    f"Recent e1RM trend: {trend_str}.\n\n"
                    f"{'Avg RPE: ' + str(bench['avg_rpe']) + ' — intensity looks appropriate.' if bench.get('avg_rpe') else 'Start logging RPE for better recommendations.'}"
                )

        if "today" in user_msg or "should i do" in user_msg:
            if exercises:
                top = exercises[0]
                return with_context(
                    f"**Today's Recommendation**\n\n"
                    f"Based on your data, focus on **{top['name']}**:\n"
                    f"• Work up to {top['pr_weight']} lbs × {max(top['pr_reps'] - 1, 5)} reps for 3-4 working sets\n"
                    f"• Target RPE 7-8 on working sets\n"
                    f"• You've logged {summary.get('workouts_this_week', 0)} workouts this week "
                    f"({summary.get('volume_this_week', 0):,.0f} lbs total volume)\n\n"
                    f"Check the Progression tab for exercise-specific weight recommendations."
                )

        return with_context(
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

    async def chat(self, message: str, history: list[dict], context: dict) -> tuple[str, list[dict], list[dict]]:
        insights = await gather_community_insights(message)
        sources = [i.to_dict() for i in insights]
        enriched = {**context, "community_insights": sources}

        exercises = context.get("exercises", [])

        detected_groups = detect_muscle_groups(message)
        if detected_groups:
            matches = [e for e in exercises if parent_muscle_group(e.get("muscle_group") or "") in detected_groups]
            enriched["muscle_group_focus"] = {
                "detected_muscle_groups": detected_groups,
                "matching_exercises": matches,
            }

        intent = extract_query_intent(message, exercises)
        if intent:
            enriched["query_intent"] = intent

        enriched["intent_classification"] = classify_intent(message)

        knowledge = await gather_knowledge_context(message)
        citations: list[dict] = []
        if knowledge:
            enriched["knowledge_base"] = knowledge
            seen_pmids: set[str] = set()
            for entry in knowledge["entries"]:
                for c in entry["citations"]:
                    if c["pmid"] not in seen_pmids:
                        citations.append({**c, "topic": entry["title"]})
                        seen_pmids.add(c["pmid"])

        messages = [{"role": m["role"], "content": m["content"]} for m in history]
        messages.append({"role": "user", "content": message})
        reply = await self.provider.generate(messages, enriched)
        return reply, sources, citations
