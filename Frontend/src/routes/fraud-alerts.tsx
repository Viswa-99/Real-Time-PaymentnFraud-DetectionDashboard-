import { createFileRoute, Link } from "@tanstack/react-router";
import { useState } from "react";
import { ALERTS, formatINR } from "@/lib/fraud/mock";
import { AppShell } from "@/components/fraud/AppShell";
import { MeterBar, Panel, PanelHeader, SeverityBadge } from "@/components/fraud/primitives";
import { cn } from "@/lib/utils";

export const Route = createFileRoute("/fraud-alerts")({
  validateSearch: (search: Record<string, unknown>): { alert?: string } =>
    typeof search["alert"] === "string" ? { alert: search["alert"] } : {},
  head: () => ({
    meta: [
      { title: "Fraud Alerts | SentinelPay" },
      {
        name: "description",
        content: "Triaged fraud alerts with severity, detection reasons and recommended actions.",
      },
      { property: "og:title", content: "Fraud Alerts | SentinelPay" },
      { property: "og:description", content: "Severity-ranked payment fraud alerts and detection reasons." },
    ],
  }),
  component: FraudAlertsPage,
});

function FraudAlertsPage() {
  const { alert } = Route.useSearch();
  const [selectedId, setSelectedId] = useState(alert ?? ALERTS[0]!.id);
  const selected = ALERTS.find((a) => a.id === selectedId) ?? ALERTS[0]!;

  return (
    <AppShell title="Fraud Alerts" subtitle="Severity-ranked detections awaiting analyst decision">
      <div className="grid gap-4 lg:grid-cols-[1.1fr_1fr]">
        <Panel>
          <PanelHeader title="Alert Queue" subtitle={`${ALERTS.length} open detections`} />
          <ul className="divide-y divide-border">
            {ALERTS.map((a) => (
              <li key={a.id}>
                <button
                  onClick={() => setSelectedId(a.id)}
                  className={cn(
                    "w-full px-5 py-3.5 text-left transition-colors hover:bg-muted/50",
                    a.id === selected.id && "bg-muted/70",
                  )}
                >
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-medium text-foreground">{a.type}</span>
                    <SeverityBadge level={a.severity} />
                    <span className="num ml-auto text-sm font-semibold text-foreground">
                      {formatINR(a.amount)}
                    </span>
                  </div>
                  <p className="num mt-0.5 text-xs text-muted-foreground">
                    {a.id} · {a.transactionId} · {a.userId} · {a.ago}
                  </p>
                  <p className="mt-0.5 text-xs text-muted-foreground">{a.reason}</p>
                  <span className="mt-2 inline-block rounded-md border border-border px-2 py-0.5 text-[11px] text-muted-foreground">
                    {a.status}
                  </span>
                </button>
              </li>
            ))}
          </ul>
        </Panel>

        <Panel className="h-fit">
          <PanelHeader
            title={`FRAUD ALERT #${selected.id}`}
            subtitle={`${selected.type} · detected ${selected.detectedAt}`}
            right={<SeverityBadge level={selected.severity} />}
          />
          <div className="grid grid-cols-2 gap-4 px-5 py-4 sm:grid-cols-3">
            <Field label="Risk Score" value={`${selected.riskScore} / 100`} critical />
            <Field label="Fraud Probability" value={`${selected.probability}%`} critical />
            <Field label="Transaction" value={selected.transactionId} />
            <Field label="User" value={selected.userId} />
            <Field label="Amount" value={formatINR(selected.amount)} />
            <Field label="Detected" value={selected.detectedAt} />
          </div>
          <div className="px-5 pb-2">
            <MeterBar value={selected.riskScore} />
          </div>
          <div className="border-t border-border px-5 py-4">
            <p className="text-xs font-semibold text-foreground">Detection reasons</p>
            <ul className="mt-2 space-y-1.5">
              {selected.reasons.map((r) => (
                <li key={r} className="flex gap-2 text-xs text-muted-foreground">
                  <span className="mt-1.5 h-1 w-1 shrink-0 rounded-full bg-critical" />
                  {r}
                </li>
              ))}
            </ul>
            <div className="mt-3 rounded-lg border border-border bg-muted/50 px-3 py-2 text-xs text-foreground">
              <span className="font-semibold">Recommended action: </span>
              {selected.recommendedAction}
            </div>
            <div className="mt-4 flex flex-wrap gap-2">
              <Link
                to="/investigation"
                search={{ tx: selected.transactionId }}
                className="rounded-lg bg-primary px-3 py-2 text-xs font-semibold text-primary-foreground"
              >
                Open Investigation
              </Link>
              <button className="rounded-lg border border-border px-3 py-2 text-xs font-medium text-foreground hover:bg-muted">
                Escalate
              </button>
              <button className="rounded-lg border border-border px-3 py-2 text-xs font-medium text-muted-foreground hover:bg-muted">
                Mark as False Positive
              </button>
            </div>
          </div>
        </Panel>
      </div>
    </AppShell>
  );
}

function Field({ label, value, critical }: { label: string; value: string; critical?: boolean }) {
  return (
    <div>
      <p className="text-[11px] text-muted-foreground">{label}</p>
      <p className={cn("num text-sm font-semibold", critical ? "text-critical" : "text-foreground")}>
        {value}
      </p>
    </div>
  );
}
