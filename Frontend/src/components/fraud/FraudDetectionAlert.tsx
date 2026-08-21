import { Link } from "@tanstack/react-router";
import { OctagonAlert } from "lucide-react";
import { DEMO_FRAUD_TX, DEMO_RISK, FRAUD_REASONS, formatINR } from "@/lib/fraud/mock";
import { Panel, PanelHeader } from "./primitives";

export function FraudDetectionAlert() {
  const tx = DEMO_FRAUD_TX;
  return (
    <Panel className="overflow-hidden border-critical/40">
      <PanelHeader
        title="Fraud Detection Alert"
        subtitle="Highest-severity event in the current session"
        icon={<OctagonAlert className="h-4 w-4 text-critical" />}
      />
      <div className="border-b border-critical/30 bg-critical-soft px-5 py-3">
        <p className="text-sm font-semibold tracking-wide text-critical">
          FRAUD PAYMENT DETECTED
        </p>
        <p className="mt-0.5 text-xs text-critical/80">
          Auto-blocked by the real-time decision engine
        </p>
      </div>
      <div className="grid grid-cols-2 gap-x-6 gap-y-1 px-5 py-4 sm:grid-cols-3">
        <Field label="Transaction" value={tx.id} />
        <Field label="Amount" value={formatINR(tx.amount)} />
        <Field label="Risk Score" value={`${tx.riskScore} / 100`} critical />
        <Field label="Risk Probability" value={`${DEMO_RISK.mlProbability}%`} critical />
        <Field label="Location" value={`${tx.location} (new)`} />
        <Field label="Status" value="BLOCKED" critical />
      </div>
      <div className="border-t border-border px-5 py-4">
        <p className="text-xs font-semibold text-foreground">Why was this transaction flagged?</p>
        <ul className="mt-2 space-y-1.5">
          {FRAUD_REASONS.map((r) => (
            <li key={r} className="flex gap-2 text-xs text-muted-foreground">
              <span className="mt-1.5 h-1 w-1 shrink-0 rounded-full bg-critical" />
              {r}
            </li>
          ))}
        </ul>
        <p className="mt-3 rounded-lg border border-border bg-muted/50 px-3 py-2 text-xs text-foreground">
          <span className="font-semibold">AI assessment:</span> High probability of account
          compromise or credential misuse.
        </p>
        <div className="mt-4 flex flex-wrap gap-2">
          <Link
            to="/investigation"
            search={{ tx: tx.id }}
            className="rounded-lg bg-critical px-3 py-2 text-xs font-semibold text-critical-foreground transition-opacity hover:opacity-90"
          >
            Investigate Transaction
          </Link>
          <Link
            to="/investigation"
            search={{ tx: tx.id }}
            className="rounded-lg border border-border px-3 py-2 text-xs font-medium text-foreground transition-colors hover:bg-muted"
          >
            View User History
          </Link>
          <button className="rounded-lg border border-border px-3 py-2 text-xs font-medium text-muted-foreground transition-colors hover:bg-muted">
            Mark as False Positive
          </button>
        </div>
      </div>
    </Panel>
  );
}

function Field({
  label,
  value,
  critical,
}: {
  label: string;
  value: string;
  critical?: boolean;
}) {
  return (
    <div className="py-1">
      <p className="text-[11px] text-muted-foreground">{label}</p>
      <p
        className={`num text-sm font-semibold ${critical ? "text-critical" : "text-foreground"}`}
      >
        {value}
      </p>
    </div>
  );
}
