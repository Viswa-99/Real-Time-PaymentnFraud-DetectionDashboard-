import type { LucideIcon } from "lucide-react";
import { cn } from "@/lib/utils";

export type KpiTone = "neutral" | "success" | "warning" | "critical" | "info";

const toneRing: Record<KpiTone, string> = {
  neutral: "bg-muted text-foreground",
  success: "bg-success-soft text-success",
  warning: "bg-warning-soft text-warning-foreground",
  critical: "bg-critical-soft text-critical",
  info: "bg-info-soft text-info",
};

export function KpiCard({
  label,
  value,
  support,
  icon: Icon,
  tone = "neutral",
}: {
  label: string;
  value: string;
  support: string;
  icon: LucideIcon;
  tone?: KpiTone;
}) {
  return (
    <div className="rounded-xl border border-border bg-card p-4">
      <div className="flex items-start justify-between gap-3">
        <p className="text-xs font-medium text-muted-foreground">{label}</p>
        <span className={cn("flex h-8 w-8 items-center justify-center rounded-lg", toneRing[tone])}>
          <Icon className="h-4 w-4" />
        </span>
      </div>
      <p className="num mt-3 text-2xl font-semibold tracking-tight text-foreground">{value}</p>
      <p
        className={cn(
          "mt-1 text-xs",
          tone === "critical"
            ? "text-critical"
            : tone === "warning"
              ? "text-warning-foreground"
              : tone === "success"
                ? "text-success"
                : "text-muted-foreground",
        )}
      >
        {support}
      </p>
    </div>
  );
}
