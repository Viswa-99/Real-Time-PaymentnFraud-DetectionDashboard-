import { Link } from "@tanstack/react-router";
import { DEMO_RISK } from "@/lib/fraud/mock";
import { MeterBar, Panel, PanelHeader } from "./primitives";
import { cn } from "@/lib/utils";

const LEVELS = ["LOW", "MEDIUM", "HIGH", "CRITICAL"] as const;

function RiskDial({ score }: { score: number }) {
  const r = 52;
  const c = 2 * Math.PI * r;
  const offset = c - (score / 100) * c;
  const stroke =
    score >= 85 ? "var(--color-critical)" : score >= 70 ? "var(--color-warning)" : "var(--color-success)";
  return (
    <div className="relative h-36 w-36">
      <svg viewBox="0 0 120 120" className="h-full w-full -rotate-90">
        <circle cx="60" cy="60" r={r} fill="none" stroke="var(--color-muted)" strokeWidth="10" />
        <circle
          cx="60"
          cy="60"
          r={r}
          fill="none"
          stroke={stroke}
          strokeWidth="10"
          strokeLinecap="round"
          strokeDasharray={c}
          strokeDashoffset={offset}
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="num text-3xl font-semibold text-foreground">{score}</span>
        <span className="num text-xs text-muted-foreground">/ 100</span>
      </div>
    </div>
  );
}

export function RiskScorePanel() {
  const risk = DEMO_RISK;
  return (
    <Panel>
      <PanelHeader title="Current Risk Score" subtitle="Aggregated portfolio risk, last 15 minutes" />
      <div className="flex flex-col items-center gap-3 px-5 py-5">
        <RiskDial score={risk.score} />
        <span className="inline-flex items-center rounded-md border border-warning/40 bg-warning-soft px-2.5 py-1 text-xs font-semibold tracking-wide text-warning-foreground">
          {risk.level} RISK
        </span>
        <div className="w-full rounded-lg border border-border p-3 text-center">
          <p className="text-xs text-muted-foreground">Risk Probability</p>
          <p className="num mt-1 text-2xl font-semibold text-foreground">{risk.probability}%</p>
          <p className="mt-0.5 text-[11px] text-muted-foreground">
            Probability of fraudulent activity
          </p>
        </div>
        <div className="w-full">
          <div className="grid grid-cols-4 gap-1">
            {LEVELS.map((l) => {
              const active = l === risk.level;
              return (
                <div key={l} className="text-center">
                  <div
                    className={cn(
                      "h-1.5 rounded-full",
                      l === "LOW"
                        ? "bg-success/30"
                        : l === "MEDIUM"
                          ? "bg-info/30"
                          : l === "HIGH"
                            ? "bg-warning/30"
                            : "bg-critical/30",
                      active &&
                        (l === "HIGH" ? "bg-warning" : l === "CRITICAL" ? "bg-critical" : "bg-info"),
                    )}
                  />
                  <span
                    className={cn(
                      "mt-1 block text-[10px] font-medium",
                      active ? "text-foreground" : "text-muted-foreground",
                    )}
                  >
                    {l}
                  </span>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </Panel>
  );
}

export function RiskFactorsPanel() {
  return (
    <Panel>
      <PanelHeader title="Risk Factors" subtitle="Signal contribution to the aggregated score" />
      <div className="space-y-3.5 px-5 py-4">
        {DEMO_RISK.factors.map((f) => (
          <div key={f.label}>
            <div className="flex items-center justify-between text-sm">
              <span className="font-medium text-foreground">{f.label}</span>
              <span className="num text-muted-foreground">{f.weight}%</span>
            </div>
            <div className="mt-1.5">
              <MeterBar value={f.weight} />
            </div>
            <p className="mt-1 text-[11px] text-muted-foreground">{f.detail}</p>
          </div>
        ))}
        <Link
          to="/investigation"
          className="mt-1 block rounded-lg border border-border px-3 py-2 text-center text-xs font-medium text-foreground transition-colors hover:bg-muted"
        >
          View Full Analysis
        </Link>
      </div>
    </Panel>
  );
}
