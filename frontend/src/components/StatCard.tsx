import clsx from "clsx";

interface StatCardProps {
  label: string;
  value: string | number;
  sub?: string;
  accent?: boolean;
  delay?: number;
}

export default function StatCard({ label, value, sub, accent }: StatCardProps) {
  return (
    <div className="panel group overflow-hidden p-5 transition-colors duration-200 hover:border-brand-400/20">
      <div
        className={clsx(
          "mb-3 h-0.5 w-8 rounded-full transition-all duration-300 group-hover:w-12",
          accent ? "bg-brand-400" : "bg-surface-border"
        )}
      />
      <p className="label mb-2">{label}</p>
      <p
        className={clsx(
          "font-display text-3xl font-semibold tracking-tight",
          accent ? "text-brand-400" : "text-ink"
        )}
      >
        {value}
      </p>
      {sub && <p className="mt-1.5 text-xs text-ink-faint">{sub}</p>}
    </div>
  );
}
