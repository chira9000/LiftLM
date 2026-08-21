from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    name: str
    created_at: datetime


class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class ExerciseOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    muscle_group: str
    equipment: str


class SetLogCreate(BaseModel):
    set_number: int
    reps: int = Field(ge=1)
    weight: float = Field(ge=0)
    rpe: float | None = Field(default=None, ge=1, le=10)
    is_warmup: bool = False


class SetLogOut(SetLogCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int


class WorkoutExerciseCreate(BaseModel):
    exercise_id: int
    order: int = 0
    notes: str | None = None
    sets: list[SetLogCreate]


class WorkoutExerciseOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    exercise_id: int
    order: int
    notes: str | None
    exercise: ExerciseOut
    sets: list[SetLogOut]


class WorkoutCreate(BaseModel):
    name: str
    notes: str | None = None
    performed_at: datetime
    exercises: list[WorkoutExerciseCreate]


class WorkoutOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    notes: str | None
    performed_at: datetime
    created_at: datetime
    exercises: list[WorkoutExerciseOut]


class WorkoutSummary(BaseModel):
    id: int
    name: str
    performed_at: datetime
    total_sets: int
    total_volume: float
    exercise_count: int


class VolumeDataPoint(BaseModel):
    date: str
    volume: float
    workout_count: int


class ExerciseTrendPoint(BaseModel):
    date: str
    estimated_1rm: float
    top_set_weight: float
    top_set_reps: int
    volume: float


class ExerciseAnalytics(BaseModel):
    exercise_id: int
    exercise_name: str
    muscle_group: str
    total_sessions: int
    total_sets: int
    total_volume: float
    estimated_1rm: float
    estimated_1rm_trend: list[ExerciseTrendPoint]
    pr_weight: float
    pr_reps: int
    pr_date: str | None
    avg_rpe: float | None
    frequency_per_week: float
    last_performed: str | None


class DashboardStats(BaseModel):
    total_workouts: int
    total_volume: float
    total_sets: int
    active_exercises: int
    workouts_this_week: int
    volume_this_week: float
    recent_prs: list[dict]
    volume_trend: list[VolumeDataPoint]
    top_exercises: list[dict]


class ProgressionRecommendation(BaseModel):
    exercise_id: int
    exercise_name: str
    recommended_weight: float
    recommended_reps: int
    recommended_sets: int
    progression_score: float
    score_breakdown: dict[str, float]
    rationale: str
    last_session_summary: dict | None


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    message: str
    history: list[ChatMessage] = []


class ChatResponse(BaseModel):
    reply: str
    context_used: dict
