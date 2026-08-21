"use client";

import { useEffect, useState } from "react";
import { Trophy } from "lucide-react";
import StatCard from "@/components/StatCard";
import PageHeader from "@/components/PageHeader";
import LoadingState from "@/components/LoadingState";
import { VolumeChart, ExerciseBarChart } from "@/components/Charts";
import { api, DashboardStats } from "@/lib/api";

export default function DashboardPage() {
  const [stats, setStats] = useState<DashboardStats | null>(null);

  useEffect(() => {
    api.dashboard().then(setStats).catch(console.error);
  }, []);

  if (!stats) return <LoadingState label="Loading dashboard" />;

  return (
    <div>
      <PageHeader title="Dashboard" subtitle="Your training overview at a glance" />

      <div className="stagger mb-6 grid grid-cols-2 gap-3 lg:grid-cols-4 lg:gap-4">
        <StatCard label="Total Workouts" value={stats.total_workouts} />
        <StatCard label="Total Volume" value={`${(stats.total_volume / 1000).toFixed(0)}k lbs`} accent />
        <StatCard
          label="This Week"
          value={stats.workouts_this_week}
          sub={`${stats.volume_this_week.toLocaleString()} lbs volume`}
        />
        <StatCard
          label="Active Exercises"
          value={stats.active_exercises}
          sub={`${stats.total_sets} total sets`}
        />
      </div>

      <div className="mb-6 grid gap-4 lg:grid-cols-3 lg:gap-5">
        <div className="panel animate-fade-up p-5 sm:p-6 lg:col-span-2" style={{ animationDelay: "0.12s" }}>
          <div className="mb-5 flex items-baseline justify-between">
            <h2 className="font-display text-lg font-semibold text-ink">Volume Trend</h2>
            <span className="text-xs text-ink-faint">All sessions</span>
          </div>
          <VolumeChart data={stats.volume_trend} />
        </div>

        <div className="panel animate-fade-up p-5 sm:p-6" style={{ animationDelay: "0.18s" }}>
          <h2 className="mb-5 flex items-center gap-2 font-display text-lg font-semibold text-ink">
            <Trophy className="h-[18px] w-[18px] text-amber-400" strokeWidth={2} />
            Recent PRs
          </h2>
          <div className="space-y-1">
            {stats.recent_prs.map((pr) => (
              <div
                key={pr.exercise}
                className="flex items-center justify-between rounded-xl px-2 py-2.5 transition-colors hover:bg-surface-hover/50"
              >
                <div className="min-w-0 pr-3">
                  <p className="truncate text-sm font-medium text-ink">{pr.exercise}</p>
                  <p className="text-xs text-ink-faint">{pr.date}</p>
                </div>
                <div className="shrink-0 text-right">
                  <p className="font-display text-sm font-semibold text-brand-400">
                    {pr.weight}×{pr.reps}
                  </p>
                  <p className="text-xs text-ink-faint">{pr.e1rm.toFixed(0)} e1RM</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="panel animate-fade-up p-5 sm:p-6" style={{ animationDelay: "0.22s" }}>
        <h2 className="mb-5 font-display text-lg font-semibold text-ink">Top Exercises by Volume</h2>
        <ExerciseBarChart data={stats.top_exercises} />
      </div>
    </div>
  );
}
