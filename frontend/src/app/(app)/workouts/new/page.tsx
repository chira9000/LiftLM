"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Plus, Trash2 } from "lucide-react";
import PageHeader from "@/components/PageHeader";
import { api, Exercise } from "@/lib/api";

interface SetEntry {
  set_number: number;
  reps: number;
  weight: number;
  rpe: number | null;
  is_warmup: boolean;
}

interface ExerciseEntry {
  exercise_id: number;
  sets: SetEntry[];
}

export default function NewWorkoutPage() {
  const router = useRouter();
  const [exercises, setExercises] = useState<Exercise[]>([]);
  const [name, setName] = useState("");
  const [date, setDate] = useState(new Date().toISOString().slice(0, 16));
  const [entries, setEntries] = useState<ExerciseEntry[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    api.exercises().then(setExercises).catch(console.error);
  }, []);

  const addExercise = () => {
    if (!exercises.length) return;
    setEntries([
      ...entries,
      {
        exercise_id: exercises[0].id,
        sets: [{ set_number: 1, reps: 8, weight: 0, rpe: null, is_warmup: false }],
      },
    ]);
  };

  const updateEntry = (idx: number, exercise_id: number) => {
    const updated = [...entries];
    updated[idx] = { ...updated[idx], exercise_id };
    setEntries(updated);
  };

  const addSet = (exIdx: number) => {
    const updated = [...entries];
    const sets = updated[exIdx].sets;
    sets.push({
      set_number: sets.length + 1,
      reps: 8,
      weight: sets[sets.length - 1]?.weight || 0,
      rpe: null,
      is_warmup: false,
    });
    setEntries(updated);
  };

  const updateSet = (
    exIdx: number,
    setIdx: number,
    field: keyof SetEntry,
    value: SetEntry[keyof SetEntry]
  ) => {
    const updated = [...entries];
    updated[exIdx] = {
      ...updated[exIdx],
      sets: updated[exIdx].sets.map((s, i) => (i === setIdx ? { ...s, [field]: value } : s)),
    };
    setEntries(updated);
  };

  const removeExercise = (idx: number) => {
    setEntries(entries.filter((_, i) => i !== idx));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      await api.createWorkout({
        name: name || "Workout",
        performed_at: new Date(date).toISOString(),
        exercises: entries.map((entry, order) => ({
          exercise_id: entry.exercise_id,
          order,
          sets: entry.sets,
        })),
      });
      router.push("/workouts");
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="mx-auto max-w-3xl">
      <PageHeader title="Log Workout" subtitle="Record sets, reps, weight, and RPE" />

      <form onSubmit={handleSubmit} className="animate-fade-up space-y-5">
        <div className="panel grid gap-4 p-5 sm:grid-cols-2 sm:p-6">
          <div>
            <label className="label mb-2 block">Workout Name</label>
            <input
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Push Day"
              className="input-field"
            />
          </div>
          <div>
            <label className="label mb-2 block">Date & Time</label>
            <input
              type="datetime-local"
              value={date}
              onChange={(e) => setDate(e.target.value)}
              className="input-field"
            />
          </div>
        </div>

        {entries.map((entry, exIdx) => (
          <div key={exIdx} className="panel space-y-4 p-5 sm:p-6">
            <div className="flex items-center justify-between gap-3">
              <select
                value={entry.exercise_id}
                onChange={(e) => updateEntry(exIdx, Number(e.target.value))}
                className="input-field max-w-xs"
              >
                {exercises.map((ex) => (
                  <option key={ex.id} value={ex.id}>
                    {ex.name}
                  </option>
                ))}
              </select>
              <button
                type="button"
                onClick={() => removeExercise(exIdx)}
                className="btn-ghost text-ink-faint hover:text-red-400"
                aria-label="Remove exercise"
              >
                <Trash2 className="h-4 w-4" />
              </button>
            </div>

            <div className="grid grid-cols-5 gap-2 px-1 text-[11px] font-medium uppercase tracking-wide text-ink-faint">
              <span>Set</span>
              <span>Reps</span>
              <span>Weight</span>
              <span>RPE</span>
              <span>WU</span>
            </div>

            {entry.sets.map((set, setIdx) => (
              <div key={setIdx} className="grid grid-cols-5 items-center gap-2">
                <span className="pl-1 text-sm text-surface-muted">{set.set_number}</span>
                <input
                  type="number"
                  value={set.reps}
                  onChange={(e) => updateSet(exIdx, setIdx, "reps", Number(e.target.value))}
                  className="input-field !px-2 !py-1.5"
                />
                <input
                  type="number"
                  value={set.weight}
                  onChange={(e) => updateSet(exIdx, setIdx, "weight", Number(e.target.value))}
                  className="input-field !px-2 !py-1.5"
                />
                <input
                  type="number"
                  step="0.5"
                  value={set.rpe ?? ""}
                  placeholder="—"
                  onChange={(e) =>
                    updateSet(exIdx, setIdx, "rpe", e.target.value ? Number(e.target.value) : null)
                  }
                  className="input-field !px-2 !py-1.5"
                />
                <input
                  type="checkbox"
                  checked={set.is_warmup}
                  onChange={(e) => updateSet(exIdx, setIdx, "is_warmup", e.target.checked)}
                  className="h-4 w-4 accent-brand-500"
                />
              </div>
            ))}

            <button
              type="button"
              onClick={() => addSet(exIdx)}
              className="text-sm font-medium text-brand-400 hover:text-brand-300"
            >
              + Add set
            </button>
          </div>
        ))}

        <button type="button" onClick={addExercise} className="btn-ghost">
          <Plus className="h-4 w-4" /> Add exercise
        </button>

        <button type="submit" disabled={loading || entries.length === 0} className="btn-primary w-full py-3">
          {loading ? "Saving..." : "Save Workout"}
        </button>
      </form>
    </div>
  );
}
