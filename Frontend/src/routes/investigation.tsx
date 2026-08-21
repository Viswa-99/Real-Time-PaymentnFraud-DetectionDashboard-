import { createFileRoute } from "@tanstack/react-router";
import { useState } from "react";
import { Search, TriangleAlert } from "lucide-react";
import { AppShell } from "@/components/fraud/AppShell";
import {
  DEMO_FRAUD_TX,
  DEMO_RISK,
  FRAUD_REASONS,
  USER_TIMELINE,
  formatINR,
} from "@/lib/fraud/mock";
import { useLiveState } from "@/lib/fraud/live-store";
import { LocationAnomalyCard } from "@/components/fraud/LocationAnomaly";
import { BehaviorCard } from "@/components/fraud/BehaviorCard";
import {
  KeyValue,
  MeterBar,
  Panel,
  PanelHeader,
  StatusBadge,
} from "@/components/fraud/primitives";
import { cn } from "@/lib/utils";

export const Route = createFileRoute("/investigation")({
  validateSearch: (search: Record<string, unknown>): { tx?: string } =>
    typeof search["tx"] === "string" ? { tx: search["tx"] } : {},
  head: () => ({
    meta: [
      { title: "Investigation Workspace | SentinelPay" },
      {
        name: "description",
        content:
          "Investigate suspicious payments with risk breakdown, behaviour timeline and explainable AI reasoning.",
      },
      { property: "og:title", content: "Investigation Workspace | SentinelPay" },
      { property: "og:description", content: "Explainable AI fraud investigation workspace." },
    ],
  }),
  component: InvestigationPage,
});

function InvestigationPage() {
  const { tx } = Route.useSearch();
  const live = useLiveState();
  const [query, setQuery] = useState(tx ?? DEMO_FRAUD_TX.id);

  const transaction =
    live.transactions.find((t) => t.id === query.trim().toUpperCase()) ??
    (tx ? live.transactions.find((t) => t.id === tx) : undefined) ??
    DEMO_FRAUD_TX;

  return (
    <AppShell
      title="Investigation"
      subtitle="Case workspace for suspicious payment activity"
    >
      <Panel className="p-4">
        <div className="flex flex-wrap items-center gap-2">
          <div className="relative min-w-64 flex-1">
            <Search className="absolute left-2.5 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-muted-foreground" />
            <input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search transaction ID / user ID / merchant ID"
              className="w-full rounded-lg border border-border bg-card py-2 pl-8 pr-3 text-sm text-foreground outline-none focus:ring-2 focus:ring-ring/40"
            />
          </div>
          <span className="text-xs text-muted-foreground">
            Showing case for <span className="num font-medium text-foreground">{transaction.id}</span>
          </span>
        </div>
      </Panel>

      <div className="grid gap-4 xl:grid-cols-3">
        <Panel className="xl:col-span-2">
          <PanelHeader
            title="Transaction Details"
            subtitle={`${transaction.merchant} · ${transaction.paymentMethod}`}
            right={<StatusBadge status={transaction.status} />}
          />
          <div className="grid gap-x-8 px-5 py-3 sm:grid-cols-2">
            <div className="divide-y divide-border">
              <KeyValue label="Transaction ID" value={transaction.id} />
              <KeyValue label="User ID" value={transaction.userId} />
              <KeyValue label="Merchant" value={transaction.merchant} />
              <KeyValue label="Amount" value={formatINR(transaction.amount)} tone="critical" />
              <KeyValue label="Timestamp" value={transaction.time} />
            </div>
            <div className="divide-y divide-border">
              <KeyValue label="Payment Method" value={transaction.paymentMethod} />
              <KeyValue label="IP Address" value={transaction.ip} />
              <KeyValue
                label="Device"
                value={transaction.device}
                tone={transaction.deviceKnown ? undefined : "critical"}
              />
              <KeyValue label="Location" value={transaction.location} />
              <KeyValue label="Risk Score" value={`${transaction.riskScore} / 100`} tone="critical" />
            </div>
          </div>
        </Panel>

        <Panel>
          <PanelHeader title="Risk Analysis" subtitle="Score composition across models" />
          <div className="space-y-3 px-5 py-4">
            <Scored label="ML fraud probability" value={DEMO_RISK.mlProbability} />
            <Scored label="Anomaly score" value={DEMO_RISK.anomalyScore} />
            <Scored label="Rule engine score" value={DEMO_RISK.ruleScore} />
            <div className="rounded-lg border border-critical/30 bg-critical-soft px-3 py-2.5">
              <p className="text-xs text-critical/90">Final risk score</p>
              <p className="num text-2xl font-semibold text-critical">
                {transaction.riskScore} / 100
              </p>
            </div>
          </div>
        </Panel>
      </div>

      <div className="grid gap-4 xl:grid-cols-3">
        <Panel className="xl:col-span-2">
          <PanelHeader
            title="Behavior Timeline"
            subtitle={`Recent activity for ${DEMO_FRAUD_TX.userId}`}
          />
          <ol className="px-5 py-4">
            {USER_TIMELINE.map((e, i) => (
              <li key={e.time} className="relative flex gap-4 pb-5 last:pb-0">
                <div className="flex flex-col items-center">
                  <span
                    className={cn(
                      "mt-1 h-2.5 w-2.5 rounded-full",
                      e.flagged ? "bg-critical" : "bg-success",
                    )}
                  />
                  {i < USER_TIMELINE.length - 1 ? (
                    <span className="w-px flex-1 bg-border" />
                  ) : null}
                </div>
                <div
                  className={cn(
                    "flex-1 rounded-lg border px-3 py-2",
                    e.flagged ? "border-critical/30 bg-critical-soft" : "border-border",
                  )}
                >
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="num text-sm font-semibold text-foreground">
                      {formatINR(e.amount)}
                    </span>
                    <span className="num text-xs text-muted-foreground">{e.time}</span>
                    <span className="text-xs text-muted-foreground">· {e.location}</span>
                    <span
                      className={cn(
                        "text-xs",
                        e.device === "New Device"
                          ? "text-critical font-medium"
                          : "text-muted-foreground",
                      )}
                    >
                      · {e.device}
                    </span>
                    {e.flagged ? (
                      <TriangleAlert className="ml-auto h-4 w-4 text-critical" />
                    ) : null}
                  </div>
                </div>
              </li>
            ))}
          </ol>
        </Panel>

        <Panel>
          <PanelHeader title="AI Explanation" subtitle="Why this transaction was flagged" />
          <div className="px-5 py-4">
            <ul className="space-y-1.5">
              {FRAUD_REASONS.map((r) => (
                <li key={r} className="flex gap-2 text-xs text-muted-foreground">
                  <span className="mt-1.5 h-1 w-1 shrink-0 rounded-full bg-critical" />
                  {r}
                </li>
              ))}
            </ul>
            <p className="mt-3 rounded-lg border border-border bg-muted/50 px-3 py-2 text-xs text-foreground">
              Multiple behavioral and contextual signals indicate a high probability of fraudulent
              activity or account compromise.
            </p>
            <div className="mt-4 grid grid-cols-2 gap-2">
              <button className="rounded-lg bg-critical px-3 py-2 text-xs font-semibold text-critical-foreground">
                Confirm Fraud
              </button>
              <button className="rounded-lg border border-success/30 bg-success-soft px-3 py-2 text-xs font-semibold text-success">
                Mark Legitimate
              </button>
              <button className="rounded-lg border border-border px-3 py-2 text-xs font-medium text-foreground hover:bg-muted">
                Escalate
              </button>
              <button className="rounded-lg border border-border px-3 py-2 text-xs font-medium text-foreground hover:bg-muted">
                Block User
              </button>
            </div>
          </div>
        </Panel>
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <LocationAnomalyCard />
        <BehaviorCard />
      </div>
    </AppShell>
  );
}

function Scored({ label, value }: { label: string; value: number }) {
  return (
    <div>
      <div className="flex items-center justify-between text-xs">
        <span className="text-muted-foreground">{label}</span>
        <span className="num font-medium text-foreground">{value}%</span>
      </div>
      <div className="mt-1.5">
        <MeterBar value={value} />
      </div>
    </div>
  );
}
