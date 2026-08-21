from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255))
    hashed_password: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    workouts: Mapped[list["Workout"]] = relationship(back_populates="user", cascade="all, delete-orphan")


class Exercise(Base):
    __tablename__ = "exercises"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    muscle_group: Mapped[str] = mapped_column(String(100))
    equipment: Mapped[str] = mapped_column(String(100), default="barbell")

    workout_exercises: Mapped[list["WorkoutExercise"]] = relationship(back_populates="exercise")


class Workout(Base):
    __tablename__ = "workouts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    name: Mapped[str] = mapped_column(String(255))
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    performed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped["User"] = relationship(back_populates="workouts")
    exercises: Mapped[list["WorkoutExercise"]] = relationship(
        back_populates="workout", cascade="all, delete-orphan", order_by="WorkoutExercise.order"
    )


class WorkoutExercise(Base):
    __tablename__ = "workout_exercises"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    workout_id: Mapped[int] = mapped_column(ForeignKey("workouts.id"), index=True)
    exercise_id: Mapped[int] = mapped_column(ForeignKey("exercises.id"), index=True)
    order: Mapped[int] = mapped_column(Integer, default=0)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    workout: Mapped["Workout"] = relationship(back_populates="exercises")
    exercise: Mapped["Exercise"] = relationship(back_populates="workout_exercises")
    sets: Mapped[list["SetLog"]] = relationship(
        back_populates="workout_exercise", cascade="all, delete-orphan", order_by="SetLog.set_number"
    )


class SetLog(Base):
    __tablename__ = "set_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    workout_exercise_id: Mapped[int] = mapped_column(ForeignKey("workout_exercises.id"), index=True)
    set_number: Mapped[int] = mapped_column(Integer)
    reps: Mapped[int] = mapped_column(Integer)
    weight: Mapped[float] = mapped_column(Float)
    rpe: Mapped[float | None] = mapped_column(Float, nullable=True)
    is_warmup: Mapped[bool] = mapped_column(default=False)

    workout_exercise: Mapped["WorkoutExercise"] = relationship(back_populates="sets")
