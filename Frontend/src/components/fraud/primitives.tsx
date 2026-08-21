import type { ReactNode } from "react";
import { cn } from "@/lib/utils";
import type { RiskLevel, TxStatus } from "@/lib/fraud/types";

export function Panel({
  className,
  children,
}: {
  className?: string;
  children: ReactNode;
}) {
  return (
    <section className={cn("rounded-xl border border-border bg-card", className)}>{children}</section>
  );
}

export function PanelHeader({
  title,
  subtitle,
  right,
  icon,
}: {
  title: string;
  subtitle?: string;
  right?: ReactNode;
  icon?: ReactNode;
}) {
  return (
    <header className="flex flex-wrap items-start justify-between gap-3 border-b border-border px-5 py-4">
      <div className="flex items-start gap-3">
        {icon ? <span className="mt-0.5 text-muted-foreground">{icon}</span> : null}
        <div>
          <h2 className="text-sm font-semibold text-foreground">{title}</h2>
          {subtitle ? <p className="mt-0.5 text-xs text-muted-foreground">{subtitle}</p> : null}
        </div>
      </div>
      {right}
    </header>
  );
}

const statusStyles: Record<TxStatus, string> = {
  SAFE: "bg-success-soft text-success border-success/25",
  REVIEW: "bg-info-soft text-info border-info/25",
  SUSPICIOUS: "bg-warning-soft text-warning-foreground border-warning/40",
  BLOCKED: "bg-critical-soft text-critical border-critical/25",
};

export function StatusBadge({ status }: { status: TxStatus }) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-md border px-2 py-0.5 text-[11px] font-semibold tracking-wide",
        statusStyles[status],
      )}
    >
      {status}
    </span>
  );
}

const levelStyles: Record<RiskLevel, string> = {
  LOW: "bg-success-soft text-success border-success/25",
  MEDIUM: "bg-info-soft text-info border-info/25",
  HIGH: "bg-warning-soft text-warning-foreground border-warning/40",
  CRITICAL: "bg-critical-soft text-critical border-critical/25",
};

export function SeverityBadge({ level }: { level: RiskLevel }) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-md border px-2 py-0.5 text-[11px] font-semibold tracking-wide",
        levelStyles[level],
      )}
    >
      {level}
    </span>
  );
}

export function riskTone(score: number) {
  if (score >= 85) return "critical";
  if (score >= 70) return "warning";
  if (score >= 45) return "info";
  return "success";
}

export function RiskPill({ score }: { score: number }) {
  const tone = riskTone(score);
  const map: Record<string, string> = {
    critical: "text-critical",
    warning: "text-warning-foreground",
    info: "text-info",
    success: "text-success",
  };
  return (
    <span className={cn("num text-sm font-semibold", map[tone])}>{score}</span>
  );
}

export function MeterBar({ value, tone }: { value: number; tone?: string }) {
  const t = tone ?? riskTone(value);
  const map: Record<string, string> = {
    critical: "bg-critical",
    warning: "bg-warning",
    info: "bg-info",
    success: "bg-success",
  };
  return (
    <div className="h-1.5 w-full overflow-hidden rounded-full bg-muted">
      <div
        className={cn("h-full rounded-full transition-all duration-500", map[t])}
        style={{ width: `${Math.min(100, Math.max(0, value))}%` }}
      />
    </div>
  );
}

export function LiveDot({ label = "LIVE" }: { label?: string }) {
  return (
    <span className="inline-flex items-center gap-1.5 rounded-md border border-success/30 bg-success-soft px-2 py-1 text-[11px] font-semibold tracking-wide text-success">
      <span className="relative flex h-1.5 w-1.5">
        <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-success opacity-75" />
        <span className="relative inline-flex h-1.5 w-1.5 rounded-full bg-success" />
      </span>
      {label}
    </span>
  );
}

export function KeyValue({ label, value, tone }: { label: string; value: ReactNode; tone?: string | undefined }) {
  const map: Record<string, string> = {
    critical: "text-critical",
    warning: "text-warning-foreground",
    success: "text-success",
    info: "text-info",
  };
  return (
    <div className="flex items-center justify-between gap-4 py-1.5 text-sm">
      <span className="text-muted-foreground">{label}</span>
      <span className={cn("num font-medium text-foreground", tone && map[tone])}>{value}</span>
    </div>
  );
}
