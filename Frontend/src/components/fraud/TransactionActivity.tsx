import { useMemo, useState } from "react";
import {
  Bar,
  CartesianGrid,
  Cell,
  ComposedChart,
  Line,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { TriangleAlert } from "lucide-react";
import { ACTIVITY, formatINR } from "@/lib/fraud/mock";
import { Panel, PanelHeader } from "./primitives";
import { cn } from "@/lib/utils";

const RANGES = [
  { key: "day", label: "Day" },
  { key: "week", label: "Week" },
  { key: "month", label: "Month" },
] as const;

type RangeKey = (typeof RANGES)[number]["key"];

export function TransactionActivity() {
  const [range, setRange] = useState<RangeKey>("day");
  const data = ACTIVITY[range];

  const { avg, spikes } = useMemo(() => {
    const mean = data.reduce((s, d) => s + d.avgAmount, 0) / data.length;
    return { avg: mean, spikes: data.filter((d) => d.avgAmount > mean * 1.35) };
  }, [data]);

  return (
    <Panel>
      <PanelHeader
        title="Transaction Activity"
        subtitle="Average transaction value and transaction volume"
        right={
          <div className="flex rounded-lg border border-border p-0.5">
            {RANGES.map((r) => (
              <button
                key={r.key}
                onClick={() => setRange(r.key)}
                className={cn(
                  "rounded-md px-3 py-1 text-xs font-medium transition-colors",
                  range === r.key
                    ? "bg-primary text-primary-foreground"
                    : "text-muted-foreground hover:text-foreground",
                )}
              >
                {r.label}
              </button>
            ))}
          </div>
        }
      />
      <div className="px-2 pt-4">
        <ResponsiveContainer width="100%" height={280}>
          <ComposedChart data={data} margin={{ top: 8, right: 16, left: 4, bottom: 4 }}>
            <CartesianGrid stroke="var(--color-border)" vertical={false} />
            <XAxis
              dataKey="label"
              tickLine={false}
              axisLine={false}
              tick={{ fontSize: 11, fill: "var(--color-muted-foreground)" }}
            />
            <YAxis
              yAxisId="left"
              tickLine={false}
              axisLine={false}
              tick={{ fontSize: 11, fill: "var(--color-muted-foreground)" }}
              tickFormatter={(v) => `₹${v}`}
            />
            <YAxis
              yAxisId="right"
              orientation="right"
              tickLine={false}
              axisLine={false}
              tick={{ fontSize: 11, fill: "var(--color-muted-foreground)" }}
            />
            <Tooltip
              contentStyle={{
                borderRadius: 10,
                border: "1px solid var(--color-border)",
                background: "var(--color-card)",
                fontSize: 12,
              }}
              formatter={(value: number, name: string) =>
                name === "Avg Transaction Amount" ? [formatINR(value), name] : [value, name]
              }
            />
            <Bar yAxisId="right" dataKey="volume" name="Transaction Volume" radius={[4, 4, 0, 0]}>
              {data.map((d) => (
                <Cell
                  key={d.label}
                  fill={
                    d.avgAmount > avg * 1.35 ? "var(--color-warning)" : "var(--color-border)"
                  }
                />
              ))}
            </Bar>
            <Line
              yAxisId="left"
              type="monotone"
              dataKey="avgAmount"
              name="Avg Transaction Amount"
              stroke="var(--color-primary)"
              strokeWidth={2}
              dot={{ r: 3 }}
            />
            <Line
              yAxisId="right"
              type="monotone"
              dataKey="suspicious"
              name="Suspicious Transactions"
              stroke="var(--color-critical)"
              strokeWidth={2}
              strokeDasharray="4 3"
              dot={false}
            />
          </ComposedChart>
        </ResponsiveContainer>
      </div>
      <div className="flex flex-wrap items-center gap-4 border-t border-border px-5 py-3 text-xs text-muted-foreground">
        <Legend color="var(--color-primary)" label="Avg transaction amount" />
        <Legend color="var(--color-border)" label="Transaction volume" />
        <Legend color="var(--color-critical)" label="Suspicious transactions" />
      </div>
      {spikes.length > 0 ? (
        <div className="mx-5 mb-5 flex items-start gap-2 rounded-lg border border-warning/40 bg-warning-soft px-3 py-2.5">
          <TriangleAlert className="mt-0.5 h-4 w-4 shrink-0 text-warning-foreground" />
          <p className="text-xs text-warning-foreground">
            <span className="font-semibold">Transaction value exceeded normal range</span> at{" "}
            {spikes.map((s) => s.label).join(", ")} — average ticket{" "}
            {formatINR(Math.round(spikes[0]!.avgAmount))} vs baseline {formatINR(Math.round(avg))}.
            Suspicious volume rose to {spikes[0]!.suspicious} events.
          </p>
        </div>
      ) : null}
    </Panel>
  );
}

function Legend({ color, label }: { color: string; label: string }) {
  return (
    <span className="inline-flex items-center gap-1.5">
      <span className="h-2 w-2 rounded-full" style={{ background: color }} />
      {label}
    </span>
  );
}
