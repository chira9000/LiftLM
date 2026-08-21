"use client";

import { useEffect, useState } from "react";
import clsx from "clsx";
import PageHeader from "@/components/PageHeader";
import LoadingState from "@/components/LoadingState";
import { ScoreBreakdown } from "@/components/Charts";
import { api, ProgressionRecommendation } from "@/lib/api";

function scoreColor(score: number) {
  if (score >= 75) return "text-brand-400";
  if (score >= 50) return "text-amber-400";
  return "text-red-400";
}

export default function ProgressionPage() {
  const [recs, setRecs] = useState<ProgressionRecommendation[] | null>(null);
  const [expanded, setExpanded] = useState<number | null>(null);

  useEffect(() => {
    api.progression().then(setRecs).catch(console.error);
  }, []);

  if (!recs) return <LoadingState label="Loading progression" />;

  return (
    <div>
      <PageHeader
        title="Progressive Overload"
        subtitle="Deterministic recommendations based on your training data"
      />

      <div className="stagger space-y-3.5">
        {recs.map((rec) => (
          <div key={rec.exercise_id} className="panel p-5 sm:p-6">
            <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
              <div className="min-w-0">
                <h3 className="font-display text-lg font-semibold text-ink">{rec.exercise_name}</h3>
                <p className="mt-1.5 max-w-xl text-sm leading-relaxed text-surface-muted">{rec.rationale}</p>
              </div>
              <div className="shrink-0 sm:text-right">
                <p className="label mb-1">Progression Score</p>
                <p className={clsx("font-display text-3xl font-semibold", scoreColor(rec.progression_score))}>
                  {rec.progression_score.toFixed(0)}
                </p>
              </div>
            </div>

            <div className="mt-5 grid grid-cols-3 gap-2.5 sm:max-w-md">
              {[
                { label: "Weight", value: `${rec.recommended_weight} lbs` },
                { label: "Reps", value: rec.recommended_reps },
                { label: "Sets", value: rec.recommended_sets },
              ].map((item) => (
                <div key={item.label} className="rounded-xl border border-surface-border bg-surface-raised px-3 py-3 text-center">
                  <p className="label mb-1">{item.label}</p>
                  <p className="font-display text-base font-semibold text-ink sm:text-lg">{item.value}</p>
                </div>
              ))}
            </div>

            <button
              type="button"
              onClick={() => setExpanded(expanded === rec.exercise_id ? null : rec.exercise_id)}
              className="mt-4 text-sm font-medium text-brand-400 transition-colors hover:text-brand-300"
            >
              {expanded === rec.exercise_id ? "Hide" : "Show"} score breakdown
            </button>

            {expanded === rec.exercise_id && (
              <div className="mt-4 animate-fade-in border-t border-surface-border pt-4">
                <ScoreBreakdown scores={rec.score_breakdown} />
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
