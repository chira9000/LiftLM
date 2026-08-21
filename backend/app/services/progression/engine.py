"""Deterministic progressive overload engine."""

from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session, joinedload

from app.models import Exercise, SetLog, Workout, WorkoutExercise
from app.schemas import ProgressionRecommendation
from app.services.analytics.engine import _working_sets, estimate_1rm


def _score_consistency(sessions: list[datetime], weeks: int = 8) -> float:
    if not sessions:
        return 0.0
    cutoff = datetime.now(timezone.utc) - timedelta(weeks=weeks)
    recent = [s for s in sessions if (s if s.tzinfo else s.replace(tzinfo=timezone.utc)) >= cutoff]
    if not recent:
        return 0.0
    # Ideal: 2x/week = 16 sessions in 8 weeks
    ideal = weeks * 2
    return min(len(recent) / ideal, 1.0) * 100


def _score_rpe(avg_rpe: float | None) -> float:
    if avg_rpe is None:
        return 60.0
    # Sweet spot 7-8.5 RPE
    if 7.0 <= avg_rpe <= 8.5:
        return 100.0
    if avg_rpe < 7.0:
        return 70.0 + avg_rpe * 3
    return max(30.0, 100.0 - (avg_rpe - 8.5) * 20)


def _score_volume_trend(volumes: list[float]) -> float:
    if len(volumes) < 2:
        return 50.0
    recent = volumes[-3:]
    older = volumes[-6:-3] if len(volumes) >= 6 else volumes[:-3]
    if not older:
        return 60.0
    recent_avg = sum(recent) / len(recent)
    older_avg = sum(older) / len(older)
    if older_avg == 0:
        return 60.0
    change = (recent_avg - older_avg) / older_avg
    return min(max(50 + change * 100, 0), 100)


def _score_progression(e1rms: list[float]) -> float:
    if len(e1rms) < 2:
        return 50.0
    first = e1rms[0]
    last = e1rms[-1]
    if first == 0:
        return 50.0
    pct = (last - first) / first
    return min(max(50 + pct * 200, 0), 100)


def _score_recent_performance(last_two_e1rm: list[float]) -> float:
    if len(last_two_e1rm) < 2:
        return 60.0
    change = last_two_e1rm[-1] - last_two_e1rm[-2]
    if change > 0:
        return min(100.0, 75 + change * 2)
    if change == 0:
        return 65.0
    return max(30.0, 65 + change * 3)


def compute_progression(db: Session, user_id: int, exercise_id: int | None = None) -> list[ProgressionRecommendation]:
    workouts = (
        db.query(Workout)
        .options(
            joinedload(Workout.exercises).joinedload(WorkoutExercise.exercise),
            joinedload(Workout.exercises).joinedload(WorkoutExercise.sets),
        )
        .filter(Workout.user_id == user_id)
        .order_by(Workout.performed_at)
        .all()
    )

    by_exercise: dict[int, dict] = {}

    for workout in workouts:
        for we in workout.exercises:
            eid = we.exercise_id
            if exercise_id and eid != exercise_id:
                continue
            working = _working_sets(we.sets)
            if not working:
                continue

            if eid not in by_exercise:
                by_exercise[eid] = {
                    "name": we.exercise.name,
                    "sessions": [],
                    "volumes": [],
                    "e1rms": [],
                    "rpe_values": [],
                    "last_working": None,
                }

            info = by_exercise[eid]
            info["sessions"].append(workout.performed_at)
            vol = sum(s.weight * s.reps for s in working)
            info["volumes"].append(vol)

            top = max(working, key=lambda s: estimate_1rm(s.weight, s.reps))
            info["e1rms"].append(estimate_1rm(top.weight, top.reps))
            info["last_working"] = working

            for s in working:
                if s.rpe is not None:
                    info["rpe_values"].append(s.rpe)

    recommendations = []

    for eid, info in by_exercise.items():
        working = info["last_working"]
        if not working:
            continue

        top_set = max(working, key=lambda s: estimate_1rm(s.weight, s.reps))
        avg_rpe = sum(info["rpe_values"]) / len(info["rpe_values"]) if info["rpe_values"] else None

        consistency = _score_consistency(info["sessions"])
        rpe_score = _score_rpe(avg_rpe)
        volume_score = _score_volume_trend(info["volumes"])
        progression_score = _score_progression(info["e1rms"])
        recent_score = _score_recent_performance(info["e1rms"])

        weights = {
            "consistency": 0.25,
            "rpe": 0.20,
            "volume": 0.20,
            "progression": 0.20,
            "recent_performance": 0.15,
        }
        breakdown = {
            "consistency": round(consistency, 1),
            "rpe": round(rpe_score, 1),
            "volume": round(volume_score, 1),
            "progression": round(progression_score, 1),
            "recent_performance": round(recent_score, 1),
        }
        total_score = sum(breakdown[k] * weights[k] for k in weights)

        # Deterministic progression rules
        rec_weight = top_set.weight
        rec_reps = top_set.reps
        rec_sets = len(working)
        rationale_parts = []

        if total_score >= 75 and avg_rpe and avg_rpe <= 8.0:
            rec_weight = round(top_set.weight + 2.5, 1)
            rec_reps = top_set.reps
            rationale_parts.append(f"Strong progression score ({total_score:.0f}). Add 2.5 lbs.")
        elif total_score >= 60:
            if top_set.reps < 8:
                rec_reps = top_set.reps + 1
                rationale_parts.append("Add a rep before increasing weight.")
            else:
                rec_weight = round(top_set.weight + 2.5, 1)
                rec_reps = max(top_set.reps - 1, 5)
                rationale_parts.append("Increase weight, drop reps slightly.")
        elif avg_rpe and avg_rpe > 9.0:
            rec_weight = round(top_set.weight * 0.95 / 2.5) * 2.5
            rec_reps = top_set.reps
            rationale_parts.append("High RPE detected — recommend deload.")
        else:
            rec_weight = top_set.weight
            rec_reps = top_set.reps
            rationale_parts.append("Maintain current load — build consistency first.")

        if consistency < 50:
            rationale_parts.append("Increase training frequency for this lift.")

        recommendations.append(
            ProgressionRecommendation(
                exercise_id=eid,
                exercise_name=info["name"],
                recommended_weight=rec_weight,
                recommended_reps=rec_reps,
                recommended_sets=rec_sets,
                progression_score=round(total_score, 1),
                score_breakdown=breakdown,
                rationale=" ".join(rationale_parts),
                last_session_summary={
                    "top_set_weight": top_set.weight,
                    "top_set_reps": top_set.reps,
                    "sets": len(working),
                    "avg_rpe": round(avg_rpe, 1) if avg_rpe else None,
                },
            )
        )

    return sorted(recommendations, key=lambda x: x.progression_score, reverse=True)
