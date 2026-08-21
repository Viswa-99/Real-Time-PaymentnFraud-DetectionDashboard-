import { createFileRoute } from "@tanstack/react-router";
import { useEffect, useMemo, useRef, useState } from "react";
import { Bar, BarChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { ConsoleShell } from "@/components/ConsoleShell";
import { Panel, RiskCell, StatCard, StatusCell } from "@/components/fraud-ui";
import { RiskDetailsModal } from "@/components/RiskDetailsModal";
import { DECISION_THRESHOLD, type Txn } from "@/lib/fraud-data";

const WS_URL = "ws://127.0.0.1:5001/ws";
export const Route = createFileRoute("/")({ component: Dashboard });

function toTxn(data: any): Txn | null {
  if (!data?.transaction_id || typeof data.risk_probability !== "number") return null;
  const tx = data.transaction ?? {};
  const blocked = data.decision === "ANOMALY" || data.risk_probability >= DECISION_THRESHOLD;
  return {
    transaction_id: data.transaction_id,
    user_id: tx.user_id ?? tx.sender_id ?? "UNKNOWN",
    receiver_id: tx.receiver_id,
    merchant_id: tx.merchant_id,
    payment_method: tx.payment_method ?? "UPI",
    transaction_type: tx.transaction_type ?? "UPI_TRANSFER",
    amount: Number(tx.amount ?? 0),
    location: tx.location_region ?? tx.location ?? "Unknown",
    device: tx.device_type ?? tx.device ?? "Unknown",
    anomaly_type: data.reasons?.[0]?.title ?? (blocked ? "COMBINED_ANOMALY" : "NONE"),
    risk_probability: data.risk_probability,
    risk_score: Number(data.risk_score ?? data.risk_probability * 100),
    layer1_anomaly_score: Number(data.layer1_anomaly_score ?? 0),
    status: blocked ? "BLOCKED" : data.risk_probability >= 0.7 ? "UNDER_REVIEW" : "APPROVED",
    timestamp: tx.timestamp ?? new Date().toISOString(),
    reasons: data.reasons ?? [],
  };
}

function Dashboard() {
  const [feed, setFeed] = useState<Txn[]>([]);
  const [live, setLive] = useState(true);
  const [connected, setConnected] = useState(false);
  const [tps, setTps] = useState(0);
  const [selectedTxn, setSelectedTxn] = useState<Txn | null>(null);
  const [mounted, setMounted] = useState(false);

  const receivedAt = useRef<number[]>([]);
  const buffer = useRef<Txn[]>([]);

  useEffect(() => {
    setMounted(true);
  }, []);

  useEffect(() => {
    if (!live) return;

    let ws: WebSocket | null = null;
    let retryTimer: ReturnType<typeof setTimeout> | null = null;

    const flushInterval = setInterval(() => {
      if (buffer.current.length > 0) {
        const next = buffer.current.splice(0);
        setFeed((current) => [...next.reverse(), ...current].slice(0, 200));
      }
    }, 100);

    const speedInterval = setInterval(() => {
      const now = Date.now();
      receivedAt.current = receivedAt.current.filter((time) => now - time <= 1000);
      setTps(receivedAt.current.length);
    }, 250);

    const connect = () => {
      try {
        const protocol = typeof window !== "undefined" && window.location.protocol === "https:" ? "wss:" : "ws:";
        const host = typeof window !== "undefined" ? window.location.host : "127.0.0.1:5001";
        ws = new WebSocket(`${protocol}//${host}/ws`);
        ws.onopen = () => setConnected(true);
        ws.onmessage = ({ data }) => {
          try {
            const event = JSON.parse(data);
            const predictions =
              event?.type === "BATCH" && Array.isArray(event.data) ? event.data : [event];
            for (const prediction of predictions) {
              const txn = toTxn(prediction);
              if (txn) {
                receivedAt.current.push(Date.now());
                buffer.current.push(txn);
              }
            }
          } catch (error) {
            console.error("Invalid ML stream event", error);
          }
        };
        ws.onclose = () => {
          setConnected(false);
          if (live) {
            retryTimer = setTimeout(connect, 1000);
          }
        };
        ws.onerror = () => ws?.close();
      } catch (e) {
        setConnected(false);
        if (live) {
          retryTimer = setTimeout(connect, 1000);
        }
      }
    };

    connect();

    return () => {
      ws?.close();
      if (retryTimer) clearTimeout(retryTimer);
      clearInterval(flushInterval);
      clearInterval(speedInterval);
    };
  }, [live]);

  const blocked = feed.filter((txn) => txn.status === "BLOCKED").length;
  const review = feed.filter((txn) => txn.status === "UNDER_REVIEW").length;

  const activity = useMemo(() => {
    return Array.from({ length: 7 }, (_, index) => {
      const now = Date.now();
      const start = now - (6 - index) * 10 * 60_000;
      const end = start + 10 * 60_000;
      const events = feed.filter((txn) => {
        const time = new Date(txn.timestamp).getTime();
        return time >= start && time < end;
      });
      return {
        bucket: index === 6 ? "now" : `-${(6 - index) * 10}m`,
        critical: events.filter((t) => t.status === "BLOCKED").length,
        high: events.filter((t) => t.status === "UNDER_REVIEW").length,
      };
    });
  }, [feed]);

  return (
    <ConsoleShell
      title="Real-Time Payments Fraud Detection Engine"
      subtitle={`Live ML decisions · auto-block threshold p ≥ ${DECISION_THRESHOLD.toFixed(2)}`}
      actions={
        <div className="flex items-center gap-3">
          <span
            className={`text-xs font-semibold px-2.5 py-1 rounded-full border ${
              connected
                ? "bg-green-500/10 text-green-400 border-green-500/20"
                : "bg-amber-500/10 text-amber-400 border-amber-500/20"
            }`}
          >
            {connected ? "⚡ ML stream connected" : "Connecting to ML stream…"}
          </span>
          <button
            onClick={() => setLive((value) => !value)}
            className="rounded-lg border border-border bg-background px-3 py-2 text-sm font-semibold hover:bg-accent transition-colors"
          >
            {live ? "⏸ Freeze stream" : "▶ Resume stream"}
          </button>
        </div>
      }
    >
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-5">
        <StatCard label="Live Processing" value={`${tps} TPS`} hint="actual scored events" />
        <StatCard label="Stream Window" value={`${feed.length} txns`} hint="last 200 ML decisions" />
        <StatCard
          label="Blocked"
          value={String(blocked)}
          tone="critical"
          hint={`p ≥ ${DECISION_THRESHOLD.toFixed(2)} auto-declined`}
        />
        <StatCard
          label="Under review"
          value={String(review)}
          tone="high"
          hint="0.70 ≤ p < threshold"
        />
        <StatCard
          label="Decision threshold"
          value={`p ≥ ${DECISION_THRESHOLD.toFixed(2)}`}
          hint="Layer 2 model"
        />
      </div>

      <div className="mt-5">
        <Panel
          title="Live ML-Scored Transactions"
          description="Transactions appear dynamically as the backend model scores them in real time"
        >
          <div className="overflow-x-auto">
            <table className="w-full min-w-[980px] text-sm">
              <thead>
                <tr className="border-b border-border text-left text-xs uppercase tracking-wider text-muted-foreground">
                  <th className="px-4 py-2.5">Status</th>
                  <th className="px-4 py-2.5">Risk score</th>
                  <th className="px-4 py-2.5">L1 score</th>
                  <th className="px-4 py-2.5">Amount</th>
                  <th className="px-4 py-2.5">Transaction</th>
                  <th className="px-4 py-2.5">User</th>
                  <th className="px-4 py-2.5">Location</th>
                  <th className="px-4 py-2.5">Reason</th>
                </tr>
              </thead>
              <tbody>
                {feed.length === 0 ? (
                  <tr>
                    <td colSpan={8} className="px-4 py-10 text-center text-muted-foreground">
                      Waiting for live ML-scored transactions. Start the simulator to populate this feed.
                    </td>
                  </tr>
                ) : (
                  feed.map((txn, index) => (
                    <tr
                      key={`${txn.transaction_id}-${index}`}
                      onClick={() => setSelectedTxn(txn)}
                      className="cursor-pointer border-b border-border/60 hover:bg-accent/70 transition-colors"
                    >
                      <td className="px-4 py-2.5">
                        <StatusCell status={txn.status} />
                      </td>
                      <td className="px-4 py-2.5">
                        <RiskCell p={txn.risk_probability} />
                      </td>
                      <td className="px-4 py-2.5 font-mono text-xs tabular-nums text-muted-foreground">
                        {txn.layer1_anomaly_score.toFixed(4)}
                      </td>
                      <td className="px-4 py-2.5 font-mono font-bold text-foreground">
                        ₹{txn.amount.toLocaleString("en-IN", { minimumFractionDigits: 2 })}
                      </td>
                      <td className="px-4 py-2.5 font-mono text-xs font-semibold">{txn.transaction_id}</td>
                      <td className="px-4 py-2.5 font-mono text-xs text-muted-foreground">{txn.user_id}</td>
                      <td className="px-4 py-2.5 text-xs">{txn.location}</td>
                      <td className="px-4 py-2.5 text-xs font-medium text-foreground">
                        {String(txn.anomaly_type).replaceAll("_", " ")}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </Panel>
      </div>

      <div className="mt-5">
        <Panel title="Recent Alert Activity" description="Calculated from the live ML stream">
          <div className="h-72 p-4">
            {mounted ? (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={activity}>
                  <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" vertical={false} />
                  <XAxis dataKey="bucket" stroke="var(--muted-foreground)" fontSize={12} />
                  <YAxis stroke="var(--muted-foreground)" fontSize={12} />
                  <Tooltip
                    contentStyle={{
                      background: "var(--background)",
                      border: "1px solid var(--border)",
                      borderRadius: "8px",
                    }}
                  />
                  <Legend />
                  <Bar dataKey="high" name="Under review" fill="var(--risk-high)" radius={[3, 3, 0, 0]} />
                  <Bar dataKey="critical" name="Blocked" fill="var(--risk-critical)" radius={[3, 3, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            ) : null}
          </div>
        </Panel>
      </div>

      <RiskDetailsModal txn={selectedTxn} onClose={() => setSelectedTxn(null)} />
    </ConsoleShell>
  );
}
