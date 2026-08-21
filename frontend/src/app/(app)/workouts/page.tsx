"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Calendar, ChevronRight, Plus } from "lucide-react";
import PageHeader from "@/components/PageHeader";
import LoadingState from "@/components/LoadingState";
import { api, WorkoutSummary } from "@/lib/api";

export default function WorkoutsPage() {
  const [workouts, setWorkouts] = useState<WorkoutSummary[] | null>(null);

  useEffect(() => {
    api.workouts().then(setWorkouts).catch(console.error);
  }, []);

  if (!workouts) return <LoadingState label="Loading workouts" />;

  return (
    <div>
      <PageHeader
        title="Workouts"
        subtitle={`${workouts.length} logged sessions`}
        action={
          <Link href="/workouts/new" className="btn-primary">
            <Plus className="h-4 w-4" />
            Log Workout
          </Link>
        }
      />

      <div className="stagger space-y-2.5">
        {workouts.map((w) => (
          <div
            key={w.id}
            className="panel-interactive flex items-center justify-between gap-4 px-4 py-4 sm:px-5"
          >
            <div className="flex min-w-0 items-center gap-3.5">
              <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-brand-500/10 text-brand-400">
                <Calendar className="h-5 w-5" strokeWidth={1.75} />
              </div>
              <div className="min-w-0">
                <p className="truncate font-medium text-ink">{w.name}</p>
                <p className="text-sm text-surface-muted">
                  {new Date(w.performed_at).toLocaleDateString("en-US", {
                    weekday: "short",
                    month: "short",
                    day: "numeric",
                    year: "numeric",
                  })}
                </p>
              </div>
            </div>
            <div className="flex shrink-0 items-center gap-4 sm:gap-6">
              <div className="hidden text-right sm:block">
                <p className="font-display font-semibold text-ink">{w.total_volume.toLocaleString()} lbs</p>
                <p className="text-xs text-ink-faint">
                  {w.total_sets} sets · {w.exercise_count} exercises
                </p>
              </div>
              <ChevronRight className="h-5 w-5 text-ink-faint" />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
