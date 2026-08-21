import { CheckCircle2, ShieldX, TriangleAlert } from "lucide-react";
import { riskBand, type Status } from "@/lib/fraud-data";
import { cn } from "@/lib/utils";

const TONE = {
  low: "bg-risk-low-soft text-risk-low",
  medium: "bg-risk-medium-soft text-risk-medium",
  high: "bg-risk-high-soft text-risk-high",
  critical: "bg-risk-critical-soft text-risk-critical",
} as const;

export function RiskCell({ p }: { p: number }) {
  const band = riskBand(p);
  return (
    <span className="flex items-center gap-2">
      <span className="font-mono text-sm tabular-nums">{(p * 100).toFixed(2)}</span>
      <span className={cn("rounded-md px-1.5 py-0.5 text-[11px] font-medium", TONE[band.tone])}>
        {band.label}
      </span>
    </span>
  );
}

export function StatusCell({ status }: { status: Status }) {
  if (status === "APPROVED")
    return (
      <span className="flex items-center gap-1.5 text-sm text-risk-low">
        <CheckCircle2 className="size-4" /> Approved
      </span>
    );
  if (status === "UNDER_REVIEW")
    return (
      <span className="flex items-center gap-1.5 text-sm text-risk-high">
        <TriangleAlert className="size-4" /> Under Review
      </span>
    );
  return (
    <span className="flex items-center gap-1.5 text-sm text-risk-critical">
      <ShieldX className="size-4" /> Blocked
    </span>
  );
}

export function StatCard({
  label,
  value,
  hint,
  tone = "neutral",
}: {
  label: string;
  value: string;
  hint?: string;
  tone?: "neutral" | "low" | "high" | "critical";
}) {
  const toneClass = {
    neutral: "text-foreground",
    low: "text-risk-low",
    high: "text-risk-high",
    critical: "text-risk-critical",
  }[tone];
  return (
    <div className="rounded-xl border border-border bg-background p-4">
      <p className="text-xs font-semibold text-muted-foreground">{label}</p>
      <p className={cn("mt-2 font-mono text-2xl font-bold tabular-nums", toneClass)}>{value}</p>
      {hint ? <p className="mt-1 text-xs text-muted-foreground">{hint}</p> : null}
    </div>
  );
}

export function Panel({
  title,
  description,
  children,
  className,
}: {
  title: string;
  description?: string;
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <section className={cn("rounded-xl border border-border bg-background", className)}>
      <header className="border-b border-border px-4 py-3">
        <h2 className="text-sm font-semibold tracking-tight">{title}</h2>
        {description ? <p className="mt-0.5 text-xs text-muted-foreground">{description}</p> : null}
      </header>
      {children}
    </section>
  );
}
