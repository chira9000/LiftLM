"""LLM service with pluggable providers (mock, ollama, mlx)."""

import json
from abc import ABC, abstractmethod

import httpx

from app.config import settings


SYSTEM_PROMPT = """You are LiftAI, an expert strength training coach. You help lifters understand their training data and make smart decisions.

You receive structured analytics about the user's training — NOT raw workout logs. Use this data to give specific, actionable advice.

Guidelines:
- Be concise but thorough (2-4 paragraphs max)
- Reference specific numbers from the analytics when relevant
- For "what should I do today" questions, give concrete sets/reps/weight recommendations
- Explain plateaus with evidence from trends, RPE, frequency, and volume
- Never invent data not present in the context
- If data is insufficient, say so and suggest what to track"""


class LLMProvider(ABC):
    @abstractmethod
    async def generate(self, messages: list[dict], context: dict) -> str:
        pass


class MockLLMProvider(LLMProvider):
    """Rule-based responses for development without a local model."""

    async def generate(self, messages: list[dict], context: dict) -> str:
        user_msg = messages[-1]["content"].lower()
        exercises = context.get("exercises", [])
        summary = context.get("summary", {})

        if "bench" in user_msg:
            bench = next((e for e in exercises if "bench" in e["name"].lower()), None)
            if bench:
                trend = bench.get("trend_last_4", [])
                trend_str = " → ".join(f"{t['e1rm']} lbs e1RM" for t in trend) if trend else "insufficient data"
                return (
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

                return (
                    f"**Squat Plateau Analysis**\n\n"
                    f"Current e1RM: **{squat['estimated_1rm']} lbs**. "
                    f"Last performed: {squat.get('last_performed', 'unknown')}.\n\n"
                    f"Likely factors:\n" + "\n".join(f"• {i}" for i in issues)
                )

        if "today" in user_msg or "should i do" in user_msg:
            if exercises:
                top = exercises[0]
                return (
                    f"**Today's Recommendation**\n\n"
                    f"Based on your data, focus on **{top['name']}**:\n"
                    f"• Work up to {top['pr_weight']} lbs × {max(top['pr_reps'] - 1, 5)} reps for 3-4 working sets\n"
                    f"• Target RPE 7-8 on working sets\n"
                    f"• You've logged {summary.get('workouts_this_week', 0)} workouts this week "
                    f"({summary.get('volume_this_week', 0):,.0f} lbs total volume)\n\n"
                    f"Check the Progression tab for exercise-specific weight recommendations."
                )

        return (
            f"**Training Overview**\n\n"
            f"You've completed **{summary.get('total_workouts', 0)} workouts** "
            f"with **{summary.get('total_volume', 0):,.0f} lbs** total volume.\n\n"
            f"Top lifts: {', '.join(e['name'] + ' (' + str(e['estimated_1rm']) + ' lbs e1RM)' for e in exercises[:3])}.\n\n"
            f"Ask me about specific exercises, today's workout, or why progress has stalled."
        )


class OllamaLLMProvider(LLMProvider):
    async def generate(self, messages: list[dict], context: dict) -> str:
        context_block = f"\n\n--- TRAINING ANALYTICS ---\n{json.dumps(context, indent=2)}\n--- END ANALYTICS ---"
        full_messages = [{"role": "system", "content": SYSTEM_PROMPT + context_block}]
        full_messages.extend(messages)

        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(
                f"{settings.llm_base_url}/api/chat",
                json={"model": settings.llm_model, "messages": full_messages, "stream": False},
            )
            resp.raise_for_status()
            return resp.json()["message"]["content"]


class MLXLLMProvider(LLMProvider):
    """Placeholder for MLX-native Qwen inference on Apple Silicon.

    To enable: pip install mlx-lm and implement generate() using mlx_lm.load/generate.
    Architecture is ready for LoRA fine-tuning via mlx-lm's adapter support.
    """

    async def generate(self, messages: list[dict], context: dict) -> str:
        try:
            from mlx_lm import generate, load  # type: ignore

            model, tokenizer = load(settings.llm_model)
            context_block = f"\n\nTraining data:\n{json.dumps(context, indent=2)}"
            prompt = SYSTEM_PROMPT + context_block + "\n\nUser: " + messages[-1]["content"] + "\nAssistant:"
            return generate(model, tokenizer, prompt=prompt, max_tokens=512)
        except ImportError:
            fallback = MockLLMProvider()
            return await fallback.generate(messages, context)


def get_llm_provider() -> LLMProvider:
    providers = {
        "mock": MockLLMProvider,
        "ollama": OllamaLLMProvider,
        "mlx": MLXLLMProvider,
    }
    cls = providers.get(settings.llm_provider, MockLLMProvider)
    return cls()


class CoachService:
    def __init__(self):
        self.provider = get_llm_provider()

    async def chat(self, message: str, history: list[dict], context: dict) -> str:
        messages = [{"role": m["role"], "content": m["content"]} for m in history]
        messages.append({"role": "user", "content": message})
        return await self.provider.generate(messages, context)
