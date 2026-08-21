import { Link } from "@tanstack/react-router";
import { ALERTS, formatINR } from "@/lib/fraud/mock";
import type { FraudAlert } from "@/lib/fraud/types";
import { Panel, PanelHeader, SeverityBadge } from "./primitives";

export function RecentAlerts({
  alerts = ALERTS,
  limit,
}: {
  alerts?: FraudAlert[];
  limit?: number;
}) {
  const rows = limit ? alerts.slice(0, limit) : alerts;
  return (
    <Panel>
      <PanelHeader
        title="Recent Fraud Alerts"
        subtitle="Triaged by severity and detection confidence"
        right={
          <Link to="/fraud-alerts" className="text-xs font-medium text-info hover:underline">
            View all
          </Link>
        }
      />
      <ul className="divide-y divide-border">
        {rows.map((a) => (
          <li key={a.id} className="flex flex-wrap items-center gap-3 px-5 py-3.5">
            <div className="min-w-52 flex-1">
              <div className="flex items-center gap-2">
                <p className="text-sm font-medium text-foreground">{a.type}</p>
                <SeverityBadge level={a.severity} />
              </div>
              <p className="num mt-0.5 text-xs text-muted-foreground">
                {a.transactionId} · {formatINR(a.amount)} · {a.ago}
              </p>
              <p className="mt-0.5 text-xs text-muted-foreground">{a.reason}</p>
            </div>
            <span className="rounded-md border border-border px-2 py-0.5 text-[11px] text-muted-foreground">
              {a.status}
            </span>
            <Link
              to="/fraud-alerts"
              search={{ alert: a.id }}
              className="rounded-lg border border-border px-3 py-1.5 text-xs font-medium text-foreground transition-colors hover:bg-muted"
            >
              {a.severity === "CRITICAL" ? "Investigate" : "Review"}
            </Link>
          </li>
        ))}
      </ul>
    </Panel>
  );
}
