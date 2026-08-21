"""Seed sample workout data for immediate testing."""

from datetime import datetime, timedelta, timezone

from app.auth import hash_password
from app.database import SessionLocal, engine
from app.models import Base, Exercise, SetLog, User, Workout, WorkoutExercise

EXERCISES = [
    ("Barbell Bench Press", "chest", "barbell"),
    ("Barbell Back Squat", "legs", "barbell"),
    ("Conventional Deadlift", "back", "barbell"),
    ("Overhead Press", "shoulders", "barbell"),
    ("Barbell Row", "back", "barbell"),
    ("Pull-ups", "back", "bodyweight"),
]


def _make_workout(db, user, name, days_ago, exercise_sets):
    performed = datetime.now(timezone.utc) - timedelta(days=days_ago)
    workout = Workout(user_id=user.id, name=name, performed_at=performed)
    db.add(workout)
    db.flush()

    for order, (exercise_name, sets) in enumerate(exercise_sets):
        exercise = db.query(Exercise).filter(Exercise.name == exercise_name).first()
        we = WorkoutExercise(workout_id=workout.id, exercise_id=exercise.id, order=order)
        db.add(we)
        db.flush()
        for i, (reps, weight, rpe, warmup) in enumerate(sets, 1):
            db.add(
                SetLog(
                    workout_exercise_id=we.id,
                    set_number=i,
                    reps=reps,
                    weight=weight,
                    rpe=rpe,
                    is_warmup=warmup,
                )
            )


def seed_database():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        if db.query(User).filter(User.email == "demo@liftai.app").first():
            return

        user = User(
            email="demo@liftai.app",
            name="Demo Lifter",
            hashed_password=hash_password("demo1234"),
        )
        db.add(user)
        db.flush()

        for name, muscle, equip in EXERCISES:
            db.add(Exercise(name=name, muscle_group=muscle, equipment=equip))
        db.flush()

        # 8 weeks of progressive sample data
        bench_prog = [
            (135, 8), (140, 8), (145, 7), (150, 7), (155, 6), (160, 6), (165, 5), (170, 5),
        ]
        squat_prog = [
            (185, 8), (195, 8), (205, 7), (205, 7), (215, 6), (215, 6), (225, 5), (225, 5),
        ]
        dead_prog = [
            (225, 6), (235, 6), (245, 5), (255, 5), (265, 4), (275, 4), (285, 3), (295, 3),
        ]

        for week in range(8):
            days_ago = 56 - week * 7
            bw, br = bench_prog[week]
            sw, sr = squat_prog[week]
            dw, dr = dead_prog[week]

            if week % 2 == 0:
                _make_workout(
                    db, user, f"Push Day — Week {week + 1}", days_ago,
                    [
                        ("Barbell Bench Press", [
                            (10, bw - 45, 5.0, True), (8, bw - 20, 6.0, True),
                            (br, bw, 7.5, False), (br - 1, bw, 8.0, False), (br - 2, bw, 8.5, False),
                        ]),
                        ("Overhead Press", [
                            (10, 65, 6.0, True), (8, 85, 7.0, False), (8, 85, 7.5, False), (7, 90, 8.0, False),
                        ]),
                    ],
                )
            else:
                _make_workout(
                    db, user, f"Pull Day — Week {week + 1}", days_ago - 2,
                    [
                        ("Conventional Deadlift", [
                            (8, dw - 90, 5.0, True), (5, dw - 45, 6.0, True),
                            (dr, dw, 7.5, False), (dr, dw, 8.0, False), (dr - 1, dw, 8.5, False),
                        ]),
                        ("Barbell Row", [
                            (10, 95, 6.0, True), (8, 115, 7.0, False), (8, 120, 7.5, False), (8, 125, 8.0, False),
                        ]),
                        ("Pull-ups", [
                            (8, 0, 6.0, False), (8, 0, 7.0, False), (7, 0, 8.0, False),
                        ]),
                    ],
                )
                _make_workout(
                    db, user, f"Leg Day — Week {week + 1}", days_ago - 4,
                    [
                        ("Barbell Back Squat", [
                            (10, sw - 65, 5.0, True), (8, sw - 35, 6.0, True),
                            (sr, sw, 7.5, False), (sr, sw, 8.0, False), (sr - 1, sw, 8.5, False),
                        ]),
                    ],
                )

        db.commit()
        print("✓ Seeded demo user (demo@liftai.app / demo1234) with 8 weeks of workout data")
    finally:
        db.close()
