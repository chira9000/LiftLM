from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from app.auth import create_access_token, get_current_user, verify_password
from app.database import get_db
from app.models import Exercise, SetLog, User, Workout, WorkoutExercise
from app.schemas import (
    ChatRequest,
    ChatResponse,
    DashboardStats,
    ExerciseAnalytics,
    ExerciseOut,
    LoginRequest,
    ProgressionRecommendation,
    TokenResponse,
    UserOut,
    WorkoutCreate,
    WorkoutOut,
    WorkoutSummary,
)
from app.services.analytics.engine import build_llm_context, compute_dashboard, compute_exercise_analytics
from app.services.llm.coach import CoachService
from app.services.progression.engine import compute_progression

router = APIRouter()


@router.post("/auth/login", response_model=TokenResponse)
def login(body: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == body.email).first()
    if not user or not verify_password(body.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token(user.id)
    return TokenResponse(access_token=token, user=UserOut.model_validate(user))


@router.get("/auth/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return UserOut.model_validate(user)


@router.get("/exercises", response_model=list[ExerciseOut])
def list_exercises(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return db.query(Exercise).order_by(Exercise.name).all()


@router.get("/workouts", response_model=list[WorkoutSummary])
def list_workouts(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    workouts = (
        db.query(Workout)
        .options(joinedload(Workout.exercises).joinedload(WorkoutExercise.sets))
        .filter(Workout.user_id == user.id)
        .order_by(Workout.performed_at.desc())
        .all()
    )
    summaries = []
    for w in workouts:
        total_sets = 0
        total_volume = 0.0
        for we in w.exercises:
            for s in we.sets:
                if not s.is_warmup:
                    total_sets += 1
                    total_volume += s.weight * s.reps
        summaries.append(
            WorkoutSummary(
                id=w.id,
                name=w.name,
                performed_at=w.performed_at,
                total_sets=total_sets,
                total_volume=round(total_volume, 1),
                exercise_count=len(w.exercises),
            )
        )
    return summaries


@router.get("/workouts/{workout_id}", response_model=WorkoutOut)
def get_workout(workout_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    workout = (
        db.query(Workout)
        .options(
            joinedload(Workout.exercises).joinedload(WorkoutExercise.exercise),
            joinedload(Workout.exercises).joinedload(WorkoutExercise.sets),
        )
        .filter(Workout.id == workout_id, Workout.user_id == user.id)
        .first()
    )
    if not workout:
        raise HTTPException(status_code=404, detail="Workout not found")
    return workout


@router.post("/workouts", response_model=WorkoutOut, status_code=201)
def create_workout(body: WorkoutCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    workout = Workout(
        user_id=user.id,
        name=body.name,
        notes=body.notes,
        performed_at=body.performed_at,
    )
    db.add(workout)
    db.flush()

    for ex_data in body.exercises:
        we = WorkoutExercise(
            workout_id=workout.id,
            exercise_id=ex_data.exercise_id,
            order=ex_data.order,
            notes=ex_data.notes,
        )
        db.add(we)
        db.flush()
        for s in ex_data.sets:
            db.add(
                SetLog(
                    workout_exercise_id=we.id,
                    set_number=s.set_number,
                    reps=s.reps,
                    weight=s.weight,
                    rpe=s.rpe,
                    is_warmup=s.is_warmup,
                )
            )

    db.commit()
    return get_workout(workout.id, db, user)


@router.get("/analytics/dashboard", response_model=DashboardStats)
def dashboard(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return compute_dashboard(db, user.id)


@router.get("/analytics/exercises", response_model=list[ExerciseAnalytics])
def exercise_analytics(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return compute_exercise_analytics(db, user.id)


@router.get("/analytics/exercises/{exercise_id}", response_model=ExerciseAnalytics)
def single_exercise_analytics(
    exercise_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    results = compute_exercise_analytics(db, user.id, exercise_id)
    if not results:
        raise HTTPException(status_code=404, detail="No data for this exercise")
    return results[0]


@router.get("/progression", response_model=list[ProgressionRecommendation])
def progression(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return compute_progression(db, user.id)


@router.get("/progression/{exercise_id}", response_model=ProgressionRecommendation)
def single_progression(
    exercise_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    results = compute_progression(db, user.id, exercise_id)
    if not results:
        raise HTTPException(status_code=404, detail="No progression data for this exercise")
    return results[0]


coach = CoachService()


@router.post("/coach/chat", response_model=ChatResponse)
async def coach_chat(body: ChatRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    context = build_llm_context(db, user.id)
    history = [{"role": m.role, "content": m.content} for m in body.history]
    reply = await coach.chat(body.message, history, context)
    return ChatResponse(reply=reply, context_used=context)
