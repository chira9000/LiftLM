export default function LoadingState({ label = "Loading" }: { label?: string }) {
  return (
    <div className="flex h-64 flex-col items-center justify-center gap-3 animate-fade-in">
      <div className="h-9 w-9 rounded-full border-2 border-surface-border border-t-brand-400 animate-spin" />
      <p className="text-sm text-surface-muted">{label}</p>
    </div>
  );
}
