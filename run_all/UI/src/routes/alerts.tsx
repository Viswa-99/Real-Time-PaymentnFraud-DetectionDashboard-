import { createFileRoute } from "@tanstack/react-router";
import { useEffect, useRef, useState } from "react";
import { ConsoleShell } from "@/components/ConsoleShell";
import { Panel, RiskCell, StatCard, StatusCell } from "@/components/fraud-ui";
import { RiskDetailsModal } from "@/components/RiskDetailsModal";
import { ANOMALY_TYPES, type Txn } from "@/lib/fraud-data";

const LAYER2_DECISION_THRESHOLD = 0.86;

export const Route = createFileRoute("/alerts")({
  head: () => ({
    meta: [
      { title: "Alert Queue & Blocked Threats Archive — Payments Fraud Detection" },
      {
        name: "description",
        content:
          "Complete persistent archive and live triage queue of all blocked UPI payment threats and anomalies.",
      },
      { property: "og:title", content: "Alert Queue & Blocked Threats Archive" },
      {
        property: "og:description",
        content: "Search, filter, and inspect all blocked UPI fraud threats in real time.",
      },
    ],
  }),
  component: Alerts,
});

function normalizeStr(str: string): string {
  return str ? str.toUpperCase().replace(/[^A-Z0-9]/g, "") : "";
}

function Alerts() {
  const [alertsFeed, setAlertsFeed] = useState<Txn[]>([]);
  const [allTimeBlocked, setAllTimeBlocked] = useState<Txn[]>([]);
  const [activeTab, setActiveTab] = useState<"BLOCKED_ARCHIVE" | "LIVE_QUEUE">("BLOCKED_ARCHIVE");
  const [filter, setFilter] = useState<string>("ALL");
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [minRisk, setMinRisk] = useState(0.30);
  const [live, setLive] = useState(true);
  const [connected, setConnected] = useState(false);
  const [selectedTxn, setSelectedTxn] = useState<Txn | null>(null);

  const queueBuffer = useRef<Txn[]>([]);
  const blockedBuffer = useRef<Txn[]>([]);
  const wsRef = useRef<WebSocket | null>(null);

  // 1. Initial Fetch of All-Time Blocked Alerts from Backend API
  useEffect(() => {
    fetch("http://127.0.0.1:5001/alerts/blocked?limit=2000")
      .then((res) => res.json())
      .then((data) => {
        if (data && data.alerts && Array.isArray(data.alerts)) {
          const formatted: Txn[] = data.alerts.map((item: any) => ({
            transaction_id: item.transaction_id || `TXN_${Date.now()}`,
            user_id: item.transaction?.user_id || item.transaction?.sender_id || "USR_01024",
            receiver_id: item.transaction?.receiver_id,
            merchant_id: item.transaction?.merchant_id,
            payment_method: item.transaction?.payment_method || "UPI",
            transaction_type: item.transaction?.transaction_type || "UPI_TRANSFER",
            amount: item.transaction?.amount || 0.0,
            location: item.transaction?.location_region || item.transaction?.location || "Chennai",
            device: item.transaction?.device_type || item.transaction?.device || "Android",
            anomaly_type: (item.reasons && item.reasons.length > 0
              ? item.reasons[0].title
              : "COMBINED_ANOMALY") as any,
            risk_probability: item.risk_probability || 0.95,
            risk_score: item.risk_score || 95.0,
            layer1_anomaly_score: item.layer1_anomaly_score || 0.55,
            status: "BLOCKED",
            timestamp: item.transaction?.timestamp || new Date().toISOString(),
            reasons: item.reasons || [],
          }));
          setAllTimeBlocked(formatted);
        }
      })
      .catch((err) => console.log("[Alerts] API fetch info:", err));
  }, []);

  // 2. Real-Time WebSocket Streaming & Permanent Blocked Store Ingestion
  useEffect(() => {
    if (!live) return;

    let ws: WebSocket | null = null;
    let retryTimer: ReturnType<typeof setTimeout> | null = null;

    const flushInterval = setInterval(() => {
      if (queueBuffer.current.length > 0) {
        const next = queueBuffer.current.splice(0);
        setAlertsFeed((current) => [...next.reverse(), ...current].slice(0, 500));
      }
      if (blockedBuffer.current.length > 0) {
        const nextBlocked = blockedBuffer.current.splice(0);
        setAllTimeBlocked((current) => {
          const existingIds = new Set(current.map((t) => t.transaction_id));
          const uniqueNew = nextBlocked.filter((t) => !existingIds.has(t.transaction_id));
          return uniqueNew.length > 0 ? [...uniqueNew.reverse(), ...current] : current;
        });
      }
    }, 100);

    const connect = () => {
      try {
        const protocol = typeof window !== "undefined" && window.location.protocol === "https:" ? "wss:" : "ws:";
        const host = typeof window !== "undefined" ? window.location.host : "127.0.0.1:5001";
        ws = new WebSocket(`${protocol}//${host}/ws`);
        wsRef.current = ws;

        ws.onopen = () => {
          setConnected(true);
        };

        ws.onmessage = (event) => {
          try {
            const raw = JSON.parse(event.data);
            const items = Array.isArray(raw)
              ? raw
              : raw && raw.type === "BATCH" && Array.isArray(raw.data)
              ? raw.data
              : [raw];

            for (const data of items) {
              if (data && data.transaction_id && data.risk_probability !== undefined) {
                const prob = data.risk_probability;
                const isBlocked = data.decision === "ANOMALY" || prob >= LAYER2_DECISION_THRESHOLD;

                const mainReason =
                  data.reasons && data.reasons.length > 0
                    ? data.reasons[0].title
                    : isBlocked
                    ? "BEHAVIORAL DRIFT"
                    : "ELEVATED RISK";

                const formattedTxn: Txn = {
                  transaction_id: data.transaction_id,
                  user_id: data.transaction?.user_id || data.transaction?.sender_id || "USR_01024",
                  receiver_id: data.transaction?.receiver_id,
                  merchant_id: data.transaction?.merchant_id,
                  payment_method: data.transaction?.payment_method || "UPI",
                  transaction_type: data.transaction?.transaction_type || "UPI_TRANSFER",
                  amount: data.transaction?.amount || 0.0,
                  location: data.transaction?.location_region || data.transaction?.location || "Chennai",
                  device: data.transaction?.device_type || data.transaction?.device || "Android",
                  anomaly_type: mainReason as any,
                  risk_probability: prob,
                  risk_score: data.risk_score,
                  layer1_anomaly_score: data.layer1_anomaly_score || 0.512,
                  status: isBlocked ? "BLOCKED" : "UNDER_REVIEW",
                  timestamp: data.transaction?.timestamp || new Date().toISOString(),
                  reasons: data.reasons || [],
                };

                if (isBlocked) {
                  blockedBuffer.current.push(formattedTxn);
                }

                if (prob >= 0.30 || isBlocked) {
                  queueBuffer.current.push(formattedTxn);
                }
              }
            }
          } catch (err) {
            console.error("[Alerts Queue] Error parsing WebSocket message:", err);
          }
        };

        ws.onclose = () => {
          setConnected(false);
          wsRef.current = null;
          if (live) {
            retryTimer = setTimeout(connect, 1000);
          }
        };

        ws.onerror = () => {
          ws?.close();
        };
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
    };
  }, [live]);

  // Source Dataset selection
  const sourceDataset = activeTab === "BLOCKED_ARCHIVE" ? allTimeBlocked : alertsFeed;

  // Search & Filter Logic
  const rows = sourceDataset.filter((t) => {
    if (activeTab === "LIVE_QUEUE" && t.risk_probability < minRisk) return false;

    // Search Query Filter
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      const matchId = t.transaction_id.toLowerCase().includes(q);
      const matchUser = t.user_id.toLowerCase().includes(q);
      const matchLoc = t.location.toLowerCase().includes(q);
      const matchDev = t.device.toLowerCase().includes(q);
      const matchType = String(t.anomaly_type).toLowerCase().includes(q);

      if (!matchId && !matchUser && !matchLoc && !matchDev && !matchType) {
        return false;
      }
    }

    if (filter === "ALL") return true;

    const normFilter = normalizeStr(filter);
    const normAnomaly = normalizeStr(String(t.anomaly_type || ""));

    return normAnomaly.includes(normFilter) || normFilter.includes(normAnomaly);
  });

  // CSV Export Function
  const exportToCSV = () => {
    const headers = [
      "Transaction ID",
      "User ID",
      "Amount (INR)",
      "Status",
      "Risk Score (%)",
      "Layer 1 Score",
      "Anomaly Reason",
      "Location",
      "Device",
      "Timestamp",
    ];
    const csvRows = rows.map((r) => [
      r.transaction_id,
      r.user_id,
      r.amount,
      r.status,
      r.risk_score.toFixed(2),
      r.layer1_anomaly_score.toFixed(4),
      `"${String(r.anomaly_type).replace(/"/g, '""')}"`,
      `"${r.location}"`,
      `"${r.device}"`,
      r.timestamp,
    ]);

    const csvContent =
      "data:text/csv;charset=utf-8," +
      [headers.join(","), ...csvRows.map((e) => e.join(","))].join("\n");

    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", `blocked_upi_alerts_${Date.now()}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <ConsoleShell
      title="Blocked Threats Archive & Live Alert Queue"
      subtitle="Permanent log of all blocked threats (Layer 2 XGBoost p ≥ 0.86) + live analyst queue"
      actions={
        <div className="flex items-center gap-3">
          <span
            className={`text-xs font-semibold px-2.5 py-1 rounded-full border ${
              connected
                ? "bg-green-500/10 text-green-400 border-green-500/20"
                : "bg-amber-500/10 text-amber-400 border-amber-500/20"
            }`}
          >
            {connected ? "⚡ Live Stream Connected" : "Connecting..."}
          </span>
          <button
            onClick={() => setLive((v) => !v)}
            className={`flex items-center gap-2 rounded-lg border px-3 py-2 text-sm font-semibold transition-all ${
              live
                ? "border-red-500/30 bg-red-500/10 text-red-400 hover:bg-red-500/20"
                : "border-green-500/30 bg-green-500/10 text-green-400 hover:bg-green-500/20"
            }`}
          >
            <span>{live ? "⏸️ Freeze Stream (Inspect)" : "▶️ Resume Stream"}</span>
          </button>
        </div>
      }
    >
      {/* Stat Cards */}
      <div className="grid gap-4 sm:grid-cols-3">
        <StatCard
          label="All-Time Blocked Threats"
          value={String(allTimeBlocked.length)}
          tone="critical"
          hint="permanently stored in memory"
        />
        <StatCard
          label="Filtered View Records"
          value={String(rows.length)}
          tone="high"
          hint="matching search & filters"
        />
        <StatCard
          label="Decision Threshold"
          value="p ≥ 0.86"
          hint="Layer 2 XGBoost auto-block"
        />
      </div>

      {/* Tab Switcher & Export */}
      <div className="mt-5 flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-2 rounded-xl border border-border bg-background p-1.5">
          <button
            onClick={() => setActiveTab("BLOCKED_ARCHIVE")}
            className={`rounded-lg px-4 py-2 text-sm font-bold transition-all ${
              activeTab === "BLOCKED_ARCHIVE"
                ? "bg-red-500 text-white shadow-md"
                : "text-muted-foreground hover:bg-accent hover:text-foreground"
            }`}
          >
            🚨 All-Time Blocked Archive ({allTimeBlocked.length})
          </button>
          <button
            onClick={() => setActiveTab("LIVE_QUEUE")}
            className={`rounded-lg px-4 py-2 text-sm font-bold transition-all ${
              activeTab === "LIVE_QUEUE"
                ? "bg-primary text-primary-foreground shadow-md"
                : "text-muted-foreground hover:bg-accent hover:text-foreground"
            }`}
          >
            ⚡ Live Alert Queue ({alertsFeed.length})
          </button>
        </div>

        <button
          onClick={exportToCSV}
          className="flex items-center gap-2 rounded-xl border border-border bg-accent/80 px-4 py-2 text-sm font-semibold hover:bg-accent transition-colors"
        >
          <span>📥 Export Blocked Alerts CSV</span>
        </button>
      </div>

      {/* Filter & Search Controls */}
      <div className="mt-4 flex flex-wrap items-center gap-3 rounded-xl border border-border bg-background p-4">
        {/* Search Input */}
        <div className="relative flex-1 min-w-[240px]">
          <input
            type="text"
            placeholder="Search by Transaction ID, User ID, Location, Reason..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full rounded-lg border border-border bg-background px-3 py-2 text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/50"
          />
          {searchQuery && (
            <button
              onClick={() => setSearchQuery("")}
              className="absolute right-3 top-2.5 text-xs text-muted-foreground hover:text-foreground"
            >
              ✕
            </button>
          )}
        </div>

        {/* Anomaly Category Filter */}
        <select
          value={filter}
          onChange={(e) => setFilter(e.target.value)}
          className="rounded-lg border border-border bg-background px-3 py-2 text-sm font-medium text-foreground"
        >
          <option value="ALL">All Anomaly Categories</option>
          {ANOMALY_TYPES.map((t) => (
            <option key={t} value={t}>
              {t}
            </option>
          ))}
        </select>

        {activeTab === "LIVE_QUEUE" && (
          <label className="flex items-center gap-3 text-sm text-muted-foreground">
            Min risk
            <input
              type="range"
              min={0.3}
              max={0.99}
              step={0.01}
              value={minRisk}
              onChange={(e) => setMinRisk(Number(e.target.value))}
              className="accent-primary"
            />
            <span className="font-mono tabular-nums text-foreground">{minRisk.toFixed(2)}</span>
          </label>
        )}

        {(filter !== "ALL" || searchQuery !== "") && (
          <button
            onClick={() => {
              setFilter("ALL");
              setSearchQuery("");
            }}
            className="rounded-lg border border-border bg-accent px-3 py-1.5 text-xs font-medium hover:bg-accent/80"
          >
            Reset Filters
          </button>
        )}
      </div>

      {/* Main Data Table */}
      <div className="mt-5">
        <Panel
          title={
            activeTab === "BLOCKED_ARCHIVE"
              ? "All-Time Persistent Blocked Threats Log (Click any row to inspect reasons)"
              : "Live Flagged Alerts Queue"
          }
          description={
            activeTab === "BLOCKED_ARCHIVE"
              ? "Permanently stored records of every auto-blocked transaction across the session"
              : "Real-time stream of incoming flagged payments"
          }
        >
          <div className="overflow-x-auto">
            <table className="w-full min-w-[860px] text-sm">
              <thead>
                <tr className="border-b border-border text-left text-xs uppercase tracking-wide text-muted-foreground">
                  <th className="px-4 py-2.5 font-medium">Status</th>
                  <th className="px-4 py-2.5 font-medium">Risk score</th>
                  <th className="px-4 py-2.5 font-medium">L1 score</th>
                  <th className="px-4 py-2.5 font-medium">Transaction ID</th>
                  <th className="px-4 py-2.5 font-medium">User ID</th>
                  <th className="px-4 py-2.5 font-medium">Amount</th>
                  <th className="px-4 py-2.5 font-medium">Flag Reason</th>
                  <th className="px-4 py-2.5 font-medium">Location</th>
                  <th className="px-4 py-2.5 text-right font-medium">Action</th>
                </tr>
              </thead>
              <tbody>
                {rows.length === 0 ? (
                  <tr>
                    <td colSpan={9} className="px-4 py-10 text-center text-sm text-muted-foreground">
                      No blocked threats match the current search & filters.
                    </td>
                  </tr>
                ) : (
                  rows.map((t, i) => (
                    <tr
                      key={t.transaction_id + i}
                      onClick={() => setSelectedTxn(t)}
                      className="border-b border-border/60 last:border-0 hover:bg-accent/70 cursor-pointer transition-colors"
                    >
                      <td className="px-4 py-2.5">
                        <StatusCell status={t.status} />
                      </td>
                      <td className="px-4 py-2.5">
                        <RiskCell p={t.risk_probability} />
                      </td>
                      <td className="px-4 py-2.5 font-mono text-xs tabular-nums text-muted-foreground">
                        {typeof t.layer1_anomaly_score === "number"
                          ? t.layer1_anomaly_score.toFixed(4)
                          : "0.5135"}
                      </td>
                      <td className="px-4 py-2.5 font-mono text-xs font-semibold text-foreground">
                        {t.transaction_id}
                      </td>
                      <td className="px-4 py-2.5 font-mono text-xs">{t.user_id}</td>
                      <td className="px-4 py-2.5 font-mono tabular-nums font-bold text-foreground">
                        ₹{t.amount.toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                      </td>
                      <td className="px-4 py-2.5 text-xs font-medium text-foreground">
                        {String(t.anomaly_type).replaceAll("_", " ")}
                      </td>
                      <td className="px-4 py-2.5 text-xs text-muted-foreground">{t.location}</td>
                      <td className="px-4 py-2.5 text-right">
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            setSelectedTxn(t);
                          }}
                          className="rounded-md bg-primary/20 border border-primary/30 px-2.5 py-1 text-xs font-semibold text-primary-foreground hover:bg-primary/30 transition-all"
                        >
                          Inspect Reasons 🔍
                        </button>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </Panel>
      </div>

      {/* THREAT INVESTIGATION MODAL */}
      <RiskDetailsModal txn={selectedTxn} onClose={() => setSelectedTxn(null)} />
    </ConsoleShell>
  );
}
