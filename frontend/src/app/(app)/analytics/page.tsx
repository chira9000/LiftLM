"use client";

import { useEffect, useState } from "react";
import clsx from "clsx";
import PageHeader from "@/components/PageHeader";
import LoadingState from "@/components/LoadingState";
import { E1RMChart } from "@/components/Charts";
import { api, ExerciseAnalytics } from "@/lib/api";

export default function AnalyticsPage() {
  const [exercises, setExercises] = useState<ExerciseAnalytics[] | null>(null);
  const [selected, setSelected] = useState<number | null>(null);

  useEffect(() => {
    api
      .exerciseAnalytics()
      .then((data) => {
        setExercises(data);
        if (data.length) setSelected(data[0].exercise_id);
      })
      .catch(console.error);
  }, []);

  if (!exercises) return <LoadingState label="Loading analytics" />;

  const current = exercises.find((e) => e.exercise_id === selected);

  return (
    <div>
      <PageHeader title="Analytics" subtitle="Performance trends and estimated 1RM" />

      <div className="grid gap-5 lg:grid-cols-4">
        <div className="stagger space-y-2">
          {exercises.map((ex) => (
            <button
              key={ex.exercise_id}
              type="button"
              onClick={() => setSelected(ex.exercise_id)}
              className={clsx(
                "w-full rounded-xl border px-4 py-3 text-left text-sm transition-all duration-200",
                selected === ex.exercise_id
                  ? "border-brand-400/35 bg-brand-500/10 text-brand-300"
                  : "border-surface-border bg-surface-card/80 text-ink-soft hover:border-brand-400/20 hover:bg-surface-hover/50"
              )}
            >
              <p className="font-medium text-ink">{ex.exercise_name}</p>
              <p className="mt-0.5 text-xs text-ink-faint">{ex.estimated_1rm} lbs e1RM</p>
            </button>
          ))}
        </div>

        {current && (
          <div className="animate-fade-up space-y-5 lg:col-span-3">
            <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
              {[
                { label: "Est. 1RM", value: `${current.estimated_1rm} lbs`, accent: true },
                { label: "PR", value: `${current.pr_weight}×${current.pr_reps}` },
                { label: "Frequency", value: `${current.frequency_per_week}x/wk` },
                { label: "Avg RPE", value: current.avg_rpe ?? "—" },
              ].map((stat) => (
                <div key={stat.label} className="panel p-4">
                  <p className="label mb-1.5">{stat.label}</p>
                  <p
                    className={clsx(
                      "font-display text-xl font-semibold",
                      stat.accent ? "text-brand-400" : "text-ink"
                    )}
                  >
                    {stat.value}
                  </p>
                </div>
              ))}
            </div>

            <div className="panel p-5 sm:p-6">
              <h2 className="mb-5 font-display text-lg font-semibold text-ink">1RM Progression</h2>
              <E1RMChart data={current.estimated_1rm_trend} />
            </div>

            <div className="panel p-5 sm:p-6">
              <h2 className="mb-4 font-display text-lg font-semibold text-ink">Session History</h2>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-surface-border text-ink-faint">
                      <th className="pb-3 text-left font-medium">Date</th>
                      <th className="pb-3 text-right font-medium">Top Set</th>
                      <th className="pb-3 text-right font-medium">e1RM</th>
                      <th className="pb-3 text-right font-medium">Volume</th>
                    </tr>
                  </thead>
                  <tbody>
                    {current.estimated_1rm_trend.map((t) => (
                      <tr
                        key={t.date}
                        className="border-b border-surface-border/40 transition-colors hover:bg-surface-hover/30"
                      >
                        <td className="py-3 text-ink-soft">{t.date}</td>
                        <td className="py-3 text-right text-ink">
                          {t.top_set_weight}×{t.top_set_reps}
                        </td>
                        <td className="py-3 text-right font-display font-semibold text-brand-400">
                          {t.estimated_1rm}
                        </td>
                        <td className="py-3 text-right text-surface-muted">{t.volume.toLocaleString()}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
