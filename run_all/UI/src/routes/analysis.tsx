import { createFileRoute } from "@tanstack/react-router";
import { useEffect, useRef, useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { ConsoleShell } from "@/components/ConsoleShell";
import { Panel, StatCard } from "@/components/fraud-ui";
import {
  DETECTION_BY_TYPE,
  FALSE_NEGATIVES,
  FALSE_POSITIVES,
  RISK_DISTRIBUTION,
  RISK_HISTOGRAM,
  TOP_LEGIT_HIGH_RISK,
  TOP_MISSED,
} from "@/lib/fraud-data";

export const Route = createFileRoute("/analysis")({
  head: () => ({
    meta: [
      { title: "Layer 2 Error Analysis — Fraud Model Performance" },
      {
        name: "description",
        content:
          "Detection rates by anomaly type, false positive and false negative distributions, and top missed anomalies from the Layer 2 fraud model.",
      },
      { property: "og:title", content: "Layer 2 Error Analysis — Fraud Model Performance" },
      {
        property: "og:description",
        content: "Detection rates by anomaly type plus false positive and negative distributions.",
      },
    ],
  }),
  component: Analysis,
});

function rateTone(rate: number) {
  if (rate >= 80) return "text-risk-low";
  if (rate >= 50) return "text-risk-high";
  return "text-risk-critical";
}

function DistTable({
  title,
  stats,
}: {
  title: string;
  stats: Record<string, number>;
}) {
  return (
    <Panel title={title}>
      <dl className="grid grid-cols-2 gap-x-4 gap-y-2 p-4 text-sm sm:grid-cols-3">
        {Object.entries(stats).map(([k, v]) => (
          <div key={k} className="flex justify-between gap-2 border-b border-border/60 pb-1">
            <dt className="text-muted-foreground">{k}</dt>
            <dd className="font-mono tabular-nums">
              {k === "count" ? v.toLocaleString() : v.toFixed(6)}
            </dd>
          </div>
        ))}
      </dl>
    </Panel>
  );
}

function Analysis() {
  const [wsConnected, setWsConnected] = useState(false);
  const [liveTxnCount, setLiveTxnCount] = useState(0);
  const [liveAnomalyCount, setLiveAnomalyCount] = useState(0);
  const [lastUpdate, setLastUpdate] = useState(new Date());
  const [mounted, setMounted] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    setMounted(true);
  }, []);

  useEffect(() => {
    let ws: WebSocket | null = null;
    let retryTimer: ReturnType<typeof setTimeout> | null = null;

    const connect = () => {
      try {
        const protocol = typeof window !== "undefined" && window.location.protocol === "https:" ? "wss:" : "ws:";
        const host = typeof window !== "undefined" ? window.location.host : "127.0.0.1:5001";
        ws = new WebSocket(`${protocol}//${host}/ws`);
        wsRef.current = ws;

        ws.onopen = () => {
          setWsConnected(true);
        };

        ws.onmessage = (event) => {
          try {
            const raw = JSON.parse(event.data);
            const items =
              raw?.type === "BATCH" && Array.isArray(raw.data)
                ? raw.data
                : Array.isArray(raw)
                ? raw
                : [raw];

            let txAdded = 0;
            let anomalyAdded = 0;
            for (const data of items) {
              if (data && data.transaction_id && data.risk_probability !== undefined) {
                txAdded++;
                if (data.decision === "ANOMALY" || data.risk_probability >= 0.86) {
                  anomalyAdded++;
                }
              }
            }
            if (txAdded > 0) {
              setLiveTxnCount((prev) => prev + txAdded);
              setLiveAnomalyCount((prev) => prev + anomalyAdded);
              setLastUpdate(new Date());
            }
          } catch (err) {
            console.error("[Analysis WS] Error parsing message:", err);
          }
        };

        ws.onclose = () => {
          setWsConnected(false);
          wsRef.current = null;
          retryTimer = setTimeout(connect, 1000);
        };

        ws.onerror = () => {
          ws?.close();
        };
      } catch (e) {
        setWsConnected(false);
        retryTimer = setTimeout(connect, 1000);
      }
    };

    connect();

    return () => {
      ws?.close();
      if (retryTimer) clearTimeout(retryTimer);
    };
  }, []);

  const updateStats = (total: number, anomalies: number) => {
    setLiveTxnCount(total);
    setLiveAnomalyCount(anomalies);
  };

  return (
    <ConsoleShell
      title="Layer 2 — Error Analysis"
      subtitle={`Scored population: ${RISK_DISTRIBUTION.count.toLocaleString()} transactions · decision threshold p ≥ 0.86`}
    >
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard
          label="Scored transactions"
          value={RISK_DISTRIBUTION.count.toLocaleString()}
          hint="mean 0.3019 · std 0.1573"
        />
        <StatCard
          label="False positives"
          value={FALSE_POSITIVES.count.toLocaleString()}
          tone="high"
          hint="legit txns scored ≥ 0.90"
        />
        <StatCard
          label="False negatives"
          value={FALSE_NEGATIVES.count.toLocaleString()}
          tone="critical"
          hint="anomalies scored < 0.90"
        />
        <StatCard
          label="p99 risk probability"
          value={RISK_DISTRIBUTION.p99.toFixed(4)}
          hint={`max ${RISK_DISTRIBUTION.max.toFixed(4)}`}
        />
        <StatCard
          label="Live processed"
          value={liveTxnCount.toLocaleString()}
          hint="via WebSocket stream"
        />
        <StatCard
          label="Live anomalies"
          value={liveAnomalyCount.toLocaleString()}
          hint="auto-blocked transactions"
        />
        <StatCard
          label="Last WS update"
          value={lastUpdate.toLocaleTimeString()}
          hint="real-time stream"
        />
      </div>

      <div className="mt-3 flex items-center gap-2">
        <span className={wsConnected ? "text-green-500" : "text-amber-500"}>
          {wsConnected ? "⚡ WS Connected" : "Connecting…"}
        </span>
      </div>

      <div className="mt-5 grid gap-5 xl:grid-cols-2">
        <Panel title="Detection by Anomaly Type">
          <div className="overflow-x-auto">
            <table className="w-full min-w-[520px] text-sm">
              <thead>
                <tr className="border-b border-border text-left text-xs uppercase tracking-wide text-muted-foreground">
                  <th className="px-4 py-2.5 font-medium">Anomaly type</th>
                  <th className="px-4 py-2.5 text-right font-medium">Count</th>
                  <th className="px-4 py-2.5 text-right font-medium">Detected</th>
                  <th className="px-4 py-2.5 text-right font-medium">Rate</th>
                  <th className="px-4 py-2.5 text-right font-medium">Mean risk</th>
                </tr>
              </thead>
              <tbody>
                {DETECTION_BY_TYPE.map((r) => (
                  <tr key={r.type} className="border-b border-border/60 last:border-0">
                    <td className="px-4 py-2.5 font-mono text-xs">{r.type}</td>
                    <td className="px-4 py-2.5 text-right font-mono tabular-nums">{r.count}</td>
                    <td className="px-4 py-2.5 text-right font-mono tabular-nums">{r.detected}</td>
                    <td
                      className={`px-4 py-2.5 text-right font-mono font-medium tabular-nums ${rateTone(r.rate)}`}
                    >
                      {r.rate.toFixed(2)}%
                    </td>
                    <td className="px-4 py-2.5 text-right font-mono tabular-nums text-muted-foreground">
                      {r.meanRisk.toFixed(4)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Panel>

        <Panel
          title="Risk Probability Distribution"
          description="Approximate population histogram of risk_probability"
        >
          <div className="h-[360px] p-4">
            {mounted ? (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={RISK_HISTOGRAM}>
                  <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" vertical={false} />
                  <XAxis dataKey="band" stroke="var(--muted-foreground)" fontSize={11} angle={-30} textAnchor="end" height={54} />
                  <YAxis stroke="var(--muted-foreground)" fontSize={11} />
                  <Tooltip
                    contentStyle={{
                      background: "var(--background)",
                      border: "1px solid var(--border)",
                      borderRadius: 8,
                      fontSize: 12,
                    }}
                  />
                  <Bar dataKey="count" name="Transactions" fill="var(--primary)" radius={[3, 3, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            ) : null}
          </div>
        </Panel>
      </div>

      <div className="mt-5 grid gap-5 xl:grid-cols-2">
        <DistTable
          title="False Positive Risk Distribution"
          stats={{
            count: FALSE_POSITIVES.count,
            mean: FALSE_POSITIVES.mean,
            std: FALSE_POSITIVES.std,
            min: FALSE_POSITIVES.min,
            "25%": FALSE_POSITIVES.p25,
            "50%": FALSE_POSITIVES.p50,
            "75%": FALSE_POSITIVES.p75,
            max: FALSE_POSITIVES.max,
          }}
        />
        <DistTable
          title="False Negative Risk Distribution"
          stats={{
            count: FALSE_NEGATIVES.count,
            mean: FALSE_NEGATIVES.mean,
            std: FALSE_NEGATIVES.std,
            min: FALSE_NEGATIVES.min,
            "25%": FALSE_NEGATIVES.p25,
            "50%": FALSE_NEGATIVES.p50,
            "75%": FALSE_NEGATIVES.p75,
            max: FALSE_NEGATIVES.max,
          }}
        />
      </div>

      <div className="mt-5 grid gap-5 xl:grid-cols-2">
        <Panel title="Top Legitimate High-Risk Transactions" description="Highest-scoring false positives">
          <div className="overflow-x-auto">
            <table className="w-full min-w-[520px] text-sm">
              <thead>
                <tr className="border-b border-border text-left text-xs uppercase tracking-wide text-muted-foreground">
                  <th className="px-4 py-2.5 font-medium">Transaction</th>
                  <th className="px-4 py-2.5 font-medium">User</th>
                  <th className="px-4 py-2.5 text-right font-medium">Risk prob.</th>
                  <th className="px-4 py-2.5 text-right font-medium">L1 score</th>
                </tr>
              </thead>
              <tbody>
                {TOP_LEGIT_HIGH_RISK.map(([txn, usr, p, , l1]) => (
                  <tr key={txn} className="border-b border-border/60 last:border-0">
                    <td className="px-4 py-2.5 font-mono text-xs">{txn}</td>
                    <td className="px-4 py-2.5 font-mono text-xs">{usr}</td>
                    <td className="px-4 py-2.5 text-right font-mono tabular-nums text-risk-critical">
                      {p.toFixed(6)}
                    </td>
                    <td className="px-4 py-2.5 text-right font-mono tabular-nums text-muted-foreground">
                      {l1.toFixed(6)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Panel>

        <Panel title="Top Missed Anomalies" description="Highest-scoring false negatives, just under threshold">
          <div className="overflow-x-auto">
            <table className="w-full min-w-[560px] text-sm">
              <thead>
                <tr className="border-b border-border text-left text-xs uppercase tracking-wide text-muted-foreground">
                  <th className="px-4 py-2.5 font-medium">Transaction</th>
                  <th className="px-4 py-2.5 font-medium">Anomaly type</th>
                  <th className="px-4 py-2.5 text-right font-medium">Risk prob.</th>
                  <th className="px-4 py-2.5 text-right font-medium">L1 score</th>
                </tr>
              </thead>
              <tbody>
                {TOP_MISSED.map(([txn, , type, p, , l1]) => (
                  <tr key={txn} className="border-b border-border/60 last:border-0">
                    <td className="px-4 py-2.5 font-mono text-xs">{txn}</td>
                    <td className="px-4 py-2.5 font-mono text-xs">{type}</td>
                    <td className="px-4 py-2.5 text-right font-mono tabular-nums text-risk-high">
                      {p.toFixed(6)}
                    </td>
                    <td className="px-4 py-2.5 text-right font-mono tabular-nums text-muted-foreground">
                      {l1.toFixed(6)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Panel>
      </div>
    </ConsoleShell>
  );
}
