import { useMemo, useState } from "react";
import { Link } from "@tanstack/react-router";
import { Search } from "lucide-react";
import { formatINR } from "@/lib/fraud/mock";
import type { Transaction } from "@/lib/fraud/types";
import { LiveDot, Panel, PanelHeader, RiskPill, StatusBadge } from "./primitives";
import { cn } from "@/lib/utils";

const RISKS = ["All", "Low", "Medium", "High", "Critical"] as const;
const STATUSES = ["All", "SAFE", "REVIEW", "SUSPICIOUS", "BLOCKED"] as const;
const TIMES = ["Last 1 hour", "Last 24 hours", "Last 7 days", "Last 30 days"] as const;
const LOCATIONS = ["All", "Hyderabad", "Bangalore", "Chennai", "Mumbai", "Delhi"] as const;

function inRisk(score: number, risk: string) {
  if (risk === "All") return true;
  if (risk === "Low") return score < 45;
  if (risk === "Medium") return score >= 45 && score < 70;
  if (risk === "High") return score >= 70 && score < 85;
  return score >= 85;
}

function Select({
  label,
  value,
  options,
  onChange,
}: {
  label: string;
  value: string;
  options: readonly string[];
  onChange: (v: string) => void;
}) {
  return (
    <label className="flex items-center gap-1.5 text-xs text-muted-foreground">
      {label}
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="rounded-md border border-border bg-card px-2 py-1.5 text-xs text-foreground outline-none focus:ring-2 focus:ring-ring/40"
      >
        {options.map((o) => (
          <option key={o} value={o}>
            {o}
          </option>
        ))}
      </select>
    </label>
  );
}

export function TransactionTable({
  transactions,
  compact = false,
  title = "Live Transaction Activity",
  subtitle = "Streaming payment events scored in real time",
}: {
  transactions: Transaction[];
  compact?: boolean;
  title?: string;
  subtitle?: string;
}) {
  const [risk, setRisk] = useState<string>("All");
  const [status, setStatus] = useState<string>("All");
  const [time, setTime] = useState<string>("Last 1 hour");
  const [location, setLocation] = useState<string>("All");
  const [query, setQuery] = useState("");

  const rows = useMemo(() => {
    const q = query.trim().toLowerCase();
    return transactions
      .filter(
        (t) =>
          inRisk(t.riskScore, risk) &&
          (status === "All" || t.status === status) &&
          (location === "All" || t.location === location) &&
          (!q ||
            t.id.toLowerCase().includes(q) ||
            t.userId.toLowerCase().includes(q) ||
            t.merchant.toLowerCase().includes(q)),
      )
      .slice(0, compact ? 8 : 60);
  }, [transactions, risk, status, location, query, compact]);

  return (
    <Panel className="overflow-hidden">
      <PanelHeader title={title} subtitle={subtitle} right={<LiveDot />} />
      <div className="flex flex-wrap items-center gap-2 border-b border-border px-5 py-3">
        <div className="relative min-w-52 flex-1">
          <Search className="absolute left-2.5 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-muted-foreground" />
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search transaction ID / user ID / merchant"
            className="w-full rounded-md border border-border bg-card py-1.5 pl-8 pr-3 text-xs text-foreground outline-none placeholder:text-muted-foreground focus:ring-2 focus:ring-ring/40"
          />
        </div>
        <Select label="Risk" value={risk} options={RISKS} onChange={setRisk} />
        <Select label="Status" value={status} options={STATUSES} onChange={setStatus} />
        <Select label="Time" value={time} options={TIMES} onChange={setTime} />
        <Select label="Location" value={location} options={LOCATIONS} onChange={setLocation} />
      </div>
      <div className="overflow-x-auto">
        <table className="w-full min-w-[860px] text-sm">
          <thead>
            <tr className="border-b border-border text-left text-[11px] uppercase tracking-wide text-muted-foreground">
              <th className="px-5 py-2.5 font-medium">Time</th>
              <th className="px-3 py-2.5 font-medium">Transaction ID</th>
              <th className="px-3 py-2.5 font-medium">User</th>
              <th className="px-3 py-2.5 font-medium">Amount</th>
              <th className="px-3 py-2.5 font-medium">Location</th>
              <th className="px-3 py-2.5 font-medium">Device</th>
              <th className="px-3 py-2.5 font-medium">Risk</th>
              <th className="px-3 py-2.5 font-medium">Status</th>
              <th className="px-5 py-2.5 font-medium" />
            </tr>
          </thead>
          <tbody>
            {rows.map((t) => (
              <tr
                key={t.id}
                className={cn(
                  "border-b border-border/70 last:border-0 transition-colors hover:bg-muted/50",
                  t.status === "BLOCKED" && "bg-critical-soft/60",
                )}
              >
                <td className="num px-5 py-2.5 text-muted-foreground">{t.time}</td>
                <td className="num px-3 py-2.5 font-medium text-foreground">{t.id}</td>
                <td className="num px-3 py-2.5 text-muted-foreground">{t.userId}</td>
                <td className="num px-3 py-2.5 font-medium text-foreground">
                  {formatINR(t.amount)}
                </td>
                <td className="px-3 py-2.5 text-muted-foreground">{t.location}</td>
                <td className="px-3 py-2.5">
                  <span
                    className={cn(
                      "text-xs",
                      t.deviceKnown ? "text-muted-foreground" : "text-warning-foreground",
                    )}
                  >
                    {t.device}
                  </span>
                </td>
                <td className="px-3 py-2.5">
                  <RiskPill score={t.riskScore} />
                </td>
                <td className="px-3 py-2.5">
                  <StatusBadge status={t.status} />
                </td>
                <td className="px-5 py-2.5 text-right">
                  <Link
                    to="/investigation"
                    search={{ tx: t.id }}
                    className="text-xs font-medium text-info hover:underline"
                  >
                    Inspect
                  </Link>
                </td>
              </tr>
            ))}
            {rows.length === 0 ? (
              <tr>
                <td colSpan={9} className="px-5 py-10 text-center text-xs text-muted-foreground">
                  No transactions match the current filters.
                </td>
              </tr>
            ) : null}
          </tbody>
        </table>
      </div>
    </Panel>
  );
}
