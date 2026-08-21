import { Link } from "@tanstack/react-router";
import { BrainCircuit } from "lucide-react";
import { MODEL_METRICS, DETECTION_FLOW } from "@/lib/fraud/mock";
import { MeterBar, Panel, PanelHeader } from "./primitives";

export function ModelInsights() {
  const m = MODEL_METRICS;
  return (
    <Panel>
      <PanelHeader
        title="AI Fraud Detection"
        subtitle="Production scoring stack and live signal weights"
        icon={<BrainCircuit className="h-4 w-4" />}
        right={
          <Link
            to="/ml-model"
            className="rounded-lg border border-border px-3 py-1.5 text-xs font-medium text-foreground transition-colors hover:bg-muted"
          >
            View Model Insights
          </Link>
        }
      />
      <div className="grid gap-5 px-5 py-4 md:grid-cols-2">
        <div>
          <div className="rounded-lg border border-border p-3">
            <p className="text-[11px] text-muted-foreground">Classifier</p>
            <p className="text-sm font-medium text-foreground">{m.model}</p>
            <p className="mt-2 text-[11px] text-muted-foreground">Anomaly model</p>
            <p className="text-sm font-medium text-foreground">{m.anomalyModel}</p>
          </div>
          <dl className="mt-3 grid grid-cols-2 gap-2">
            <Metric label="Accuracy" value={`${m.accuracy}%`} />
            <Metric label="Precision" value={`${m.precision}%`} />
            <Metric label="Recall" value={`${m.recall}%`} />
            <Metric label="F1 Score" value={`${m.f1}%`} />
            <Metric label="False Positive Rate" value={`${m.falsePositiveRate}%`} />
            <Metric label="Model version" value="v2.4.1" />
          </dl>
        </div>
        <div>
          <p className="text-xs font-semibold text-foreground">Detection Signals</p>
          <div className="mt-3 space-y-2.5">
            {m.signals.map((s) => (
              <div key={s.name}>
                <div className="flex items-center justify-between text-xs">
                  <span className="text-muted-foreground">{s.name}</span>
                  <span className="num text-foreground">{s.strength}%</span>
                </div>
                <div className="mt-1">
                  <MeterBar value={s.strength} />
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </Panel>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg border border-border px-3 py-2">
      <dt className="text-[11px] text-muted-foreground">{label}</dt>
      <dd className="num text-sm font-semibold text-foreground">{value}</dd>
    </div>
  );
}

export function DetectionFlow() {
  return (
    <Panel>
      <PanelHeader title="Fraud Detection Flow" subtitle="How every payment is scored end to end" />
      <div className="flex flex-wrap items-center gap-2 px-5 py-5">
        {DETECTION_FLOW.map((step, i) => (
          <div key={step} className="flex items-center gap-2">
            <span className="rounded-lg border border-border bg-muted/50 px-3 py-2 text-xs font-medium text-foreground">
              {step}
            </span>
            {i < DETECTION_FLOW.length - 1 ? (
              <span className="text-muted-foreground">→</span>
            ) : null}
          </div>
        ))}
      </div>
      <div className="flex flex-wrap gap-2 border-t border-border px-5 py-4">
        <span className="rounded-md border border-success/25 bg-success-soft px-3 py-1.5 text-xs font-semibold text-success">
          APPROVE
        </span>
        <span className="rounded-md border border-warning/40 bg-warning-soft px-3 py-1.5 text-xs font-semibold text-warning-foreground">
          REVIEW
        </span>
        <span className="rounded-md border border-critical/25 bg-critical-soft px-3 py-1.5 text-xs font-semibold text-critical">
          BLOCK
        </span>
        <p className="ml-auto self-center text-[11px] text-muted-foreground">
          Decision latency p95: 84 ms
        </p>
      </div>
    </Panel>
  );
}
