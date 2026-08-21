"""Deterministic analytics engine — no LLM involvement."""

from collections import defaultdict
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session, joinedload

from app.models import Exercise, SetLog, Workout, WorkoutExercise
from app.schemas import (
    DashboardStats,
    ExerciseAnalytics,
    ExerciseTrendPoint,
    VolumeDataPoint,
)


def estimate_1rm(weight: float, reps: int) -> float:
    """Epley formula for estimated 1RM."""
    if reps <= 0 or weight <= 0:
        return 0.0
    if reps == 1:
        return weight
    return weight * (1 + reps / 30)


def _working_sets(sets: list[SetLog]) -> list[SetLog]:
    return [s for s in sets if not s.is_warmup]


def _get_user_sets(db: Session, user_id: int) -> list[tuple[Workout, WorkoutExercise, SetLog, Exercise]]:
    rows = (
        db.query(Workout, WorkoutExercise, SetLog, Exercise)
        .join(WorkoutExercise, WorkoutExercise.workout_id == Workout.id)
        .join(SetLog, SetLog.workout_exercise_id == WorkoutExercise.id)
        .join(Exercise, Exercise.id == WorkoutExercise.exercise_id)
        .filter(Workout.user_id == user_id)
        .order_by(Workout.performed_at)
        .all()
    )
    return rows


def compute_dashboard(db: Session, user_id: int) -> DashboardStats:
    rows = _get_user_sets(db, user_id)
    now = datetime.now(timezone.utc)
    week_ago = now - timedelta(days=7)

    workout_ids = set()
    volume_by_date: dict[str, float] = defaultdict(float)
    workout_count_by_date: dict[str, int] = defaultdict(int)
    exercise_volumes: dict[str, float] = defaultdict(float)
    prs: list[dict] = []

    total_volume = 0.0
    total_sets = 0
    workouts_this_week = set()
    volume_this_week = 0.0

    # Track PRs per exercise
    exercise_best: dict[int, dict] = {}

    for workout, we, s, exercise in rows:
        if s.is_warmup:
            continue

        workout_ids.add(workout.id)
        vol = s.weight * s.reps
        total_volume += vol
        total_sets += 1

        date_key = workout.performed_at.strftime("%Y-%m-%d")
        volume_by_date[date_key] += vol

        exercise_volumes[exercise.name] += vol

        performed = workout.performed_at
        if performed.tzinfo is None:
            performed = performed.replace(tzinfo=timezone.utc)

        if performed >= week_ago:
            workouts_this_week.add(workout.id)
            volume_this_week += vol

        e1rm = estimate_1rm(s.weight, s.reps)
        best = exercise_best.get(exercise.id)
        if best is None or e1rm > best["e1rm"]:
            exercise_best[exercise.id] = {
                "exercise": exercise.name,
                "weight": s.weight,
                "reps": s.reps,
                "e1rm": e1rm,
                "date": date_key,
            }

    for w_id in workout_ids:
        # count workouts per date
        pass

    # Re-count workouts per date
    workouts = db.query(Workout).filter(Workout.user_id == user_id).all()
    for w in workouts:
        date_key = w.performed_at.strftime("%Y-%m-%d")
        workout_count_by_date[date_key] += 1

    volume_trend = [
        VolumeDataPoint(date=d, volume=round(volume_by_date[d], 1), workout_count=workout_count_by_date.get(d, 0))
        for d in sorted(volume_by_date.keys())
    ]

    top_exercises = sorted(
        [{"name": k, "volume": round(v, 1)} for k, v in exercise_volumes.items()],
        key=lambda x: x["volume"],
        reverse=True,
    )[:5]

    recent_prs = sorted(exercise_best.values(), key=lambda x: x["e1rm"], reverse=True)[:5]

    return DashboardStats(
        total_workouts=len(workout_ids),
        total_volume=round(total_volume, 1),
        total_sets=total_sets,
        active_exercises=len(exercise_volumes),
        workouts_this_week=len(workouts_this_week),
        volume_this_week=round(volume_this_week, 1),
        recent_prs=recent_prs,
        volume_trend=volume_trend,
        top_exercises=top_exercises,
    )


def compute_exercise_analytics(db: Session, user_id: int, exercise_id: int | None = None) -> list[ExerciseAnalytics]:
    query = (
        db.query(Workout)
        .options(
            joinedload(Workout.exercises).joinedload(WorkoutExercise.exercise),
            joinedload(Workout.exercises).joinedload(WorkoutExercise.sets),
        )
        .filter(Workout.user_id == user_id)
        .order_by(Workout.performed_at)
    )
    workouts = query.all()

    by_exercise: dict[int, dict] = defaultdict(lambda: {
        "sessions": 0,
        "sets": [],
        "trend": [],
        "dates": [],
    })

    for workout in workouts:
        for we in workout.exercises:
            eid = we.exercise_id
            if exercise_id and eid != exercise_id:
                continue

            working = _working_sets(we.sets)
            if not working:
                continue

            info = by_exercise[eid]
            info["sessions"] += 1
            info["dates"].append(workout.performed_at)
            info["exercise"] = we.exercise

            session_volume = sum(s.weight * s.reps for s in working)
            top_set = max(working, key=lambda s: estimate_1rm(s.weight, s.reps))
            session_e1rm = estimate_1rm(top_set.weight, top_set.reps)

            info["trend"].append(
                ExerciseTrendPoint(
                    date=workout.performed_at.strftime("%Y-%m-%d"),
                    estimated_1rm=round(session_e1rm, 1),
                    top_set_weight=top_set.weight,
                    top_set_reps=top_set.reps,
                    volume=round(session_volume, 1),
                )
            )
            info["sets"].extend(working)

    results = []
    for eid, info in by_exercise.items():
        exercise = info["exercise"]
        sets = info["sets"]
        if not sets:
            continue

        total_volume = sum(s.weight * s.reps for s in sets)
        top = max(sets, key=lambda s: estimate_1rm(s.weight, s.reps))
        e1rm = estimate_1rm(top.weight, top.reps)

        rpe_values = [s.rpe for s in sets if s.rpe is not None]
        avg_rpe = round(sum(rpe_values) / len(rpe_values), 1) if rpe_values else None

        dates = info["dates"]
        if len(dates) >= 2:
            span_days = max((dates[-1] - dates[0]).days, 1)
            freq = len(dates) / (span_days / 7)
        else:
            freq = len(dates)

        results.append(
            ExerciseAnalytics(
                exercise_id=eid,
                exercise_name=exercise.name,
                muscle_group=exercise.muscle_group,
                total_sessions=info["sessions"],
                total_sets=len(sets),
                total_volume=round(total_volume, 1),
                estimated_1rm=round(e1rm, 1),
                estimated_1rm_trend=info["trend"],
                pr_weight=top.weight,
                pr_reps=top.reps,
                pr_date=dates[-1].strftime("%Y-%m-%d") if dates else None,
                avg_rpe=avg_rpe,
                frequency_per_week=round(freq, 2),
                last_performed=dates[-1].strftime("%Y-%m-%d") if dates else None,
            )
        )

    return sorted(results, key=lambda x: x.total_volume, reverse=True)


def build_llm_context(db: Session, user_id: int) -> dict:
    """Structured analytics payload for the LLM — not raw workout logs."""
    dashboard = compute_dashboard(db, user_id)
    exercises = compute_exercise_analytics(db, user_id)

    return {
        "summary": {
            "total_workouts": dashboard.total_workouts,
            "total_volume": dashboard.total_volume,
            "workouts_this_week": dashboard.workouts_this_week,
            "volume_this_week": dashboard.volume_this_week,
        },
        "recent_prs": dashboard.recent_prs,
        "top_exercises": dashboard.top_exercises,
        "volume_trend_last_8": dashboard.volume_trend[-8:],
        "exercises": [
            {
                "name": e.exercise_name,
                "muscle_group": e.muscle_group,
                "estimated_1rm": e.estimated_1rm,
                "pr_weight": e.pr_weight,
                "pr_reps": e.pr_reps,
                "total_sessions": e.total_sessions,
                "frequency_per_week": e.frequency_per_week,
                "avg_rpe": e.avg_rpe,
                "last_performed": e.last_performed,
                "trend_last_4": [
                    {"date": t.date, "e1rm": t.estimated_1rm, "volume": t.volume}
                    for t in e.estimated_1rm_trend[-4:]
                ],
            }
            for e in exercises
        ],
    }
