import { createFileRoute } from "@tanstack/react-router";
import { useState } from "react";
import { AppShell } from "@/components/fraud/AppShell";
import { LOCATION_RISK, formatINR } from "@/lib/fraud/mock";
import { Panel, PanelHeader, RiskPill } from "@/components/fraud/primitives";
import { cn } from "@/lib/utils";

export const Route = createFileRoute("/fraud-map")({
  head: () => ({
    meta: [
      { title: "Fraud Map | SentinelPay" },
      {
        name: "description",
        content: "Geographic view of payment activity, suspicious clusters and confirmed fraud events.",
      },
      { property: "og:title", content: "Fraud Map | SentinelPay" },
      { property: "og:description", content: "Geospatial fraud and transaction risk intelligence." },
    ],
  }),
  component: FraudMapPage,
});

interface Marker {
  id: string;
  city: string;
  user: string;
  amount: number;
  risk: number;
  reason: string;
  time: string;
  tone: "safe" | "suspicious" | "fraud";
  lat: number;
  lng: number;
}

const MARKERS: Marker[] = [
  {
    id: "TXN-84922",
    city: "Chennai",
    user: "USR-1024",
    amount: 42000,
    risk: 91,
    reason: "Impossible Travel",
    time: "10:42:36",
    tone: "fraud",
    lat: 13.0827,
    lng: 80.2707,
  },
  {
    id: "TXN-84871",
    city: "Mumbai",
    user: "USR-2210",
    amount: 52000,
    risk: 93,
    reason: "Impossible Travel",
    time: "10:28:44",
    tone: "fraud",
    lat: 19.076,
    lng: 72.8777,
  },
  {
    id: "TXN-84840",
    city: "Delhi",
    user: "USR-5583",
    amount: 27800,
    risk: 78,
    reason: "New device + high value",
    time: "10:21:02",
    tone: "suspicious",
    lat: 28.6139,
    lng: 77.209,
  },
  {
    id: "TXN-84921",
    city: "Hyderabad",
    user: "USR-1024",
    amount: 2400,
    risk: 18,
    reason: "Within user baseline",
    time: "10:42:31",
    tone: "safe",
    lat: 17.385,
    lng: 78.4867,
  },
  {
    id: "TXN-84923",
    city: "Bangalore",
    user: "USR-3192",
    amount: 8500,
    risk: 63,
    reason: "Above average ticket size",
    time: "10:42:41",
    tone: "suspicious",
    lat: 12.9716,
    lng: 77.5946,
  },
];

const BOUNDS = { minLat: 8, maxLat: 32, minLng: 68, maxLng: 92 };
const toXY = (lat: number, lng: number) => ({
  x: ((lng - BOUNDS.minLng) / (BOUNDS.maxLng - BOUNDS.minLng)) * 100,
  y: ((BOUNDS.maxLat - lat) / (BOUNDS.maxLat - BOUNDS.minLat)) * 100,
});

const toneColor = {
  safe: "var(--color-success)",
  suspicious: "var(--color-warning)",
  fraud: "var(--color-critical)",
} as const;

function FraudMapPage() {
  const [selected, setSelected] = useState<Marker>(MARKERS[0]!);

  return (
    <AppShell title="Fraud Map" subtitle="Geographic distribution of payment risk across India">
      <div className="grid gap-4 lg:grid-cols-[1.6fr_1fr]">
        <Panel>
          <PanelHeader
            title="Transaction Geography"
            subtitle="Green = normal · Orange = suspicious · Red = fraud"
          />
          <div className="p-5">
            <div className="relative aspect-[4/3] w-full overflow-hidden rounded-lg border border-border bg-muted/40">
              <svg viewBox="0 0 100 100" className="absolute inset-0 h-full w-full">
                {[20, 40, 60, 80].map((v) => (
                  <g key={v}>
                    <line x1={v} y1="0" x2={v} y2="100" stroke="var(--color-border)" strokeWidth="0.2" />
                    <line x1="0" y1={v} x2="100" y2={v} stroke="var(--color-border)" strokeWidth="0.2" />
                  </g>
                ))}
                <path
                  d="M28 12 L58 8 L74 22 L70 46 L54 78 L42 92 L30 62 L18 40 Z"
                  fill="var(--color-muted)"
                  stroke="var(--color-border)"
                  strokeWidth="0.4"
                />
              </svg>
              {MARKERS.map((m) => {
                const { x, y } = toXY(m.lat, m.lng);
                return (
                  <button
                    key={m.id}
                    onClick={() => setSelected(m)}
                    style={{ left: `${x}%`, top: `${y}%`, color: toneColor[m.tone] }}
                    className="absolute -translate-x-1/2 -translate-y-1/2"
                    aria-label={`${m.city} ${m.id}`}
                  >
                    <span className="relative flex h-3.5 w-3.5 items-center justify-center">
                      <span
                        className="absolute h-6 w-6 rounded-full opacity-20"
                        style={{ background: "currentColor" }}
                      />
                      <span
                        className={cn(
                          "h-3 w-3 rounded-full border-2 border-card",
                          selected.id === m.id && "ring-2 ring-foreground/40",
                        )}
                        style={{ background: "currentColor" }}
                      />
                    </span>
                    <span className="mt-1 block text-[10px] font-medium text-foreground">
                      {m.city}
                    </span>
                  </button>
                );
              })}
            </div>
            <div className="mt-4 rounded-lg border border-border p-4">
              <div className="flex items-center justify-between">
                <p className="num text-sm font-semibold text-foreground">{selected.id}</p>
                <RiskPill score={selected.risk} />
              </div>
              <div className="mt-2 grid grid-cols-2 gap-2 text-xs sm:grid-cols-3">
                <Cell label="User" value={selected.user} />
                <Cell label="Amount" value={formatINR(selected.amount)} />
                <Cell label="Location" value={selected.city} />
                <Cell label="Risk Score" value={`${selected.risk} / 100`} />
                <Cell label="Detection reason" value={selected.reason} />
                <Cell label="Timestamp" value={selected.time} />
              </div>
            </div>
          </div>
        </Panel>

        <Panel className="h-fit">
          <PanelHeader title="Location Risk Summary" subtitle="Last 24 hours by city" />
          <ul className="divide-y divide-border">
            {LOCATION_RISK.map((l) => {
              const rate = (l.suspicious / l.transactions) * 100;
              return (
                <li key={l.city} className="flex items-center justify-between px-5 py-3">
                  <div>
                    <p className="text-sm font-medium text-foreground">{l.city}</p>
                    <p className="num text-xs text-muted-foreground">
                      {l.transactions.toLocaleString("en-IN")} transactions
                    </p>
                  </div>
                  <div className="text-right">
                    <p
                      className={cn(
                        "num text-sm font-semibold",
                        rate > 1 ? "text-critical" : "text-warning-foreground",
                      )}
                    >
                      {l.suspicious} suspicious
                    </p>
                    <p className="num text-xs text-muted-foreground">{rate.toFixed(2)}% flag rate</p>
                  </div>
                </li>
              );
            })}
          </ul>
        </Panel>
      </div>
    </AppShell>
  );
}

function Cell({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="text-[11px] text-muted-foreground">{label}</p>
      <p className="num text-xs font-medium text-foreground">{value}</p>
    </div>
  );
}
