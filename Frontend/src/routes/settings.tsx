import { createFileRoute } from "@tanstack/react-router";
import { AppShell } from "@/components/fraud/AppShell";
import { Panel, PanelHeader } from "@/components/fraud/primitives";
import { API_BASE_URL } from "@/lib/fraud/api";

export const Route = createFileRoute("/settings")({
  head: () => ({
    meta: [
      { title: "Settings | SentinelPay" },
      {
        name: "description",
        content: "Configure fraud thresholds, alerting channels and backend API connectivity.",
      },
      { property: "og:title", content: "Settings | SentinelPay" },
      { property: "og:description", content: "Fraud platform thresholds and integration settings." },
    ],
  }),
  component: SettingsPage,
});

function Row({
  label,
  hint,
  control,
}: {
  label: string;
  hint: string;
  control: React.ReactNode;
}) {
  return (
    <div className="flex flex-wrap items-center justify-between gap-3 py-3.5">
      <div>
        <p className="text-sm font-medium text-foreground">{label}</p>
        <p className="text-xs text-muted-foreground">{hint}</p>
      </div>
      {control}
    </div>
  );
}

function SettingsPage() {
  const input =
    "rounded-lg border border-border bg-card px-3 py-1.5 text-sm text-foreground outline-none focus:ring-2 focus:ring-ring/40";
  return (
    <AppShell title="Settings" subtitle="Detection thresholds, alerting and API integration">
      <div className="grid gap-4 lg:grid-cols-2">
        <Panel>
          <PanelHeader title="Detection Thresholds" subtitle="Applied to the live decision engine" />
          <div className="divide-y divide-border px-5">
            <Row label="Block threshold" hint="Auto-block transactions at or above this risk score" control={<input className={`${input} num w-20`} defaultValue={85} />} />
            <Row label="Review threshold" hint="Route to analyst queue at or above this score" control={<input className={`${input} num w-20`} defaultValue={45} />} />
            <Row label="Velocity window" hint="Transactions per user in rolling window" control={<input className={`${input} w-28`} defaultValue="10 minutes" />} />
            <Row label="Impossible travel speed" hint="Flag above this required travel speed" control={<input className={`${input} w-28`} defaultValue="900 km/h" />} />
          </div>
        </Panel>

        <Panel>
          <PanelHeader title="Alerting" subtitle="Where critical detections are delivered" />
          <div className="divide-y divide-border px-5">
            <Row label="In-app notifications" hint="Critical fraud events in the header bell" control={<Toggle defaultOn />} />
            <Row label="Email digest" hint="Hourly summary to the fraud operations group" control={<Toggle defaultOn />} />
            <Row label="Webhook" hint="POST critical alerts to your SOC endpoint" control={<input className={`${input} w-56`} defaultValue="https://soc.internal/fraud-hook" />} />
            <Row label="Auto-escalate CRITICAL" hint="Create a case immediately on detection" control={<Toggle defaultOn />} />
          </div>
        </Panel>
      </div>

      <Panel>
        <PanelHeader title="Backend Integration" subtitle="FastAPI endpoints consumed by this frontend" />
        <div className="px-5 py-4">
          <p className="text-xs text-muted-foreground">
            Base URL: <span className="num font-medium text-foreground">{API_BASE_URL}</span> ·
            currently serving mock data
          </p>
          <ul className="mt-3 grid gap-1.5 font-mono text-xs text-muted-foreground sm:grid-cols-2">
            {[
              "GET /transactions",
              "GET /transactions/{id}",
              "GET /alerts",
              "GET /alerts/{id}",
              "GET /risk/{transaction_id}",
              "GET /analytics",
              "GET /model/metrics",
              "GET /users/{id}/transactions",
              "WS  /ws/transactions",
            ].map((e) => (
              <li key={e} className="rounded-md border border-border px-2.5 py-1.5">
                {e}
              </li>
            ))}
          </ul>
        </div>
      </Panel>
    </AppShell>
  );
}

function Toggle({ defaultOn }: { defaultOn?: boolean }) {
  return (
    <label className="inline-flex cursor-pointer items-center">
      <input type="checkbox" defaultChecked={defaultOn} className="peer sr-only" />
      <span className="relative h-5 w-9 rounded-full bg-muted transition-colors peer-checked:bg-success after:absolute after:left-0.5 after:top-0.5 after:h-4 after:w-4 after:rounded-full after:bg-card after:transition-all peer-checked:after:translate-x-4" />
    </label>
  );
}
