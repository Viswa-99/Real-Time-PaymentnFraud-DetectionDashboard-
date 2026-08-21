import { createFileRoute } from "@tanstack/react-router";
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { AppShell } from "@/components/fraud/AppShell";
import { TransactionActivity } from "@/components/fraud/TransactionActivity";
import { Panel, PanelHeader } from "@/components/fraud/primitives";
import { LOCATION_RISK } from "@/lib/fraud/mock";

export const Route = createFileRoute("/analytics")({
  head: () => ({
    meta: [
      { title: "Fraud Analytics | SentinelPay" },
      {
        name: "description",
        content: "Fraud trend analytics: detection rate, anomaly mix, velocity and location flag rates.",
      },
      { property: "og:title", content: "Fraud Analytics | SentinelPay" },
      { property: "og:description", content: "Payment fraud trend and detection analytics." },
    ],
  }),
  component: AnalyticsPage,
});

const TREND = [
  { label: "Week 1", detected: 21, blocked: 12, falsePositive: 6 },
  { label: "Week 2", detected: 26, blocked: 15, falsePositive: 5 },
  { label: "Week 3", detected: 29, blocked: 17, falsePositive: 5 },
  { label: "Week 4", detected: 34, blocked: 18, falsePositive: 4 },
];

const MIX = [
  { name: "Impossible travel", value: 28, color: "var(--color-critical)" },
  { name: "Velocity anomaly", value: 24, color: "var(--color-warning)" },
  { name: "Amount deviation", value: 22, color: "var(--color-info)" },
  { name: "Device anomaly", value: 16, color: "var(--color-primary)" },
  { name: "Merchant risk", value: 10, color: "var(--color-success)" },
];

function AnalyticsPage() {
  return (
    <AppShell title="Analytics" subtitle="Fraud trends, anomaly composition and location risk">
      <TransactionActivity />

      <div className="grid gap-4 lg:grid-cols-2">
        <Panel>
          <PanelHeader title="Fraud Detection Trend" subtitle="Detected vs blocked vs false positives" />
          <div className="px-2 py-4">
            <ResponsiveContainer width="100%" height={260}>
              <AreaChart data={TREND}>
                <CartesianGrid stroke="var(--color-border)" vertical={false} />
                <XAxis dataKey="label" tickLine={false} axisLine={false} tick={{ fontSize: 11 }} />
                <YAxis tickLine={false} axisLine={false} tick={{ fontSize: 11 }} />
                <Tooltip
                  contentStyle={{
                    borderRadius: 10,
                    border: "1px solid var(--color-border)",
                    background: "var(--color-card)",
                    fontSize: 12,
                  }}
                />
                <Area
                  type="monotone"
                  dataKey="detected"
                  stroke="var(--color-critical)"
                  fill="var(--color-critical)"
                  fillOpacity={0.12}
                />
                <Area
                  type="monotone"
                  dataKey="blocked"
                  stroke="var(--color-primary)"
                  fill="var(--color-primary)"
                  fillOpacity={0.1}
                />
                <Area
                  type="monotone"
                  dataKey="falsePositive"
                  stroke="var(--color-success)"
                  fill="var(--color-success)"
                  fillOpacity={0.1}
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </Panel>

        <Panel>
          <PanelHeader title="Anomaly Composition" subtitle="Share of detections by signal type" />
          <div className="grid gap-2 px-2 py-4 sm:grid-cols-[1fr_auto] sm:items-center">
            <ResponsiveContainer width="100%" height={240}>
              <PieChart>
                <Pie data={MIX} dataKey="value" innerRadius={58} outerRadius={92} paddingAngle={2}>
                  {MIX.map((m) => (
                    <Cell key={m.name} fill={m.color} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{
                    borderRadius: 10,
                    border: "1px solid var(--color-border)",
                    background: "var(--color-card)",
                    fontSize: 12,
                  }}
                />
              </PieChart>
            </ResponsiveContainer>
            <ul className="space-y-1.5 px-4 text-xs">
              {MIX.map((m) => (
                <li key={m.name} className="flex items-center gap-2 text-muted-foreground">
                  <span className="h-2 w-2 rounded-full" style={{ background: m.color }} />
                  {m.name}
                  <span className="num ml-auto font-medium text-foreground">{m.value}%</span>
                </li>
              ))}
            </ul>
          </div>
        </Panel>
      </div>

      <Panel>
        <PanelHeader title="Suspicious Volume By Location" subtitle="Flagged transactions per city" />
        <div className="px-2 py-4">
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={LOCATION_RISK}>
              <CartesianGrid stroke="var(--color-border)" vertical={false} />
              <XAxis dataKey="city" tickLine={false} axisLine={false} tick={{ fontSize: 11 }} />
              <YAxis tickLine={false} axisLine={false} tick={{ fontSize: 11 }} />
              <Tooltip
                contentStyle={{
                  borderRadius: 10,
                  border: "1px solid var(--color-border)",
                  background: "var(--color-card)",
                  fontSize: 12,
                }}
              />
              <Bar dataKey="suspicious" radius={[4, 4, 0, 0]} fill="var(--color-warning)" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </Panel>
    </AppShell>
  );
}
