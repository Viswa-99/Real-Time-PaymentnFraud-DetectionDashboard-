import { createFileRoute } from "@tanstack/react-router";
import { AppShell } from "@/components/fraud/AppShell";
import { DetectionFlow, ModelInsights } from "@/components/fraud/ModelInsights";
import { MeterBar, Panel, PanelHeader } from "@/components/fraud/primitives";
import { MODEL_METRICS } from "@/lib/fraud/mock";

export const Route = createFileRoute("/ml-model")({
  head: () => ({
    meta: [
      { title: "ML Model | SentinelPay" },
      {
        name: "description",
        content: "Fraud model performance, feature importance and scoring pipeline configuration.",
      },
      { property: "og:title", content: "ML Model | SentinelPay" },
      { property: "og:description", content: "Fraud detection model metrics and feature importance." },
    ],
  }),
  component: MlModelPage,
});

const FEATURES = [
  { name: "amount_to_user_avg_ratio", importance: 0.24 },
  { name: "geo_velocity_kmh", importance: 0.19 },
  { name: "txn_count_10min", importance: 0.16 },
  { name: "device_fingerprint_age_days", importance: 0.13 },
  { name: "merchant_risk_index", importance: 0.1 },
  { name: "hour_of_day_deviation", importance: 0.09 },
  { name: "ip_asn_reputation", importance: 0.09 },
];

function MlModelPage() {
  const m = MODEL_METRICS;
  return (
    <AppShell title="ML Model" subtitle="Scoring stack, performance and feature attribution">
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-5">
        {[
          ["Accuracy", `${m.accuracy}%`],
          ["Precision", `${m.precision}%`],
          ["Recall", `${m.recall}%`],
          ["F1 Score", `${m.f1}%`],
          ["False Positive Rate", `${m.falsePositiveRate}%`],
        ].map(([label, value]) => (
          <div key={label} className="rounded-xl border border-border bg-card p-4">
            <p className="text-xs text-muted-foreground">{label}</p>
            <p className="num mt-2 text-2xl font-semibold text-foreground">{value}</p>
          </div>
        ))}
      </div>

      <ModelInsights />

      <div className="grid gap-4 lg:grid-cols-2">
        <Panel>
          <PanelHeader title="Feature Importance" subtitle="Global SHAP contribution, last retrain" />
          <div className="space-y-3 px-5 py-4">
            {FEATURES.map((f) => (
              <div key={f.name}>
                <div className="flex items-center justify-between text-xs">
                  <span className="font-mono text-muted-foreground">{f.name}</span>
                  <span className="num text-foreground">{(f.importance * 100).toFixed(0)}%</span>
                </div>
                <div className="mt-1.5">
                  <MeterBar value={f.importance * 100 * 3} tone="info" />
                </div>
              </div>
            ))}
          </div>
        </Panel>

        <Panel>
          <PanelHeader title="Pipeline Configuration" subtitle="Runtime thresholds and retraining" />
          <div className="divide-y divide-border px-5 py-2 text-sm">
            {[
              ["Classifier", m.model],
              ["Anomaly detector", m.anomalyModel],
              ["Block threshold", "Risk ≥ 85"],
              ["Review threshold", "Risk ≥ 45"],
              ["Scoring latency (p95)", "84 ms"],
              ["Retrain cadence", "Weekly, on labelled outcomes"],
              ["Last retrain", "3 days ago · 2.1M transactions"],
              ["Drift status", "Stable (PSI 0.06)"],
            ].map(([k, v]) => (
              <div key={k} className="flex items-center justify-between gap-4 py-2.5">
                <span className="text-muted-foreground">{k}</span>
                <span className="num text-right font-medium text-foreground">{v}</span>
              </div>
            ))}
          </div>
        </Panel>
      </div>

      <DetectionFlow />
    </AppShell>
  );
}
