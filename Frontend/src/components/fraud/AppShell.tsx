import { Link, useRouterState } from "@tanstack/react-router";
import {
  Activity,
  Bell,
  BrainCircuit,
  ChartNoAxesCombined,
  LayoutDashboard,
  Map,
  Search,
  Settings,
  ShieldAlert,
  ShieldCheck,
  UserRound,
} from "lucide-react";
import { useState, type ReactNode } from "react";
import { cn } from "@/lib/utils";
import { useLiveState } from "@/lib/fraud/live-store";
import { LiveDot } from "./primitives";

const NAV = [
  { to: "/", label: "Dashboard", icon: LayoutDashboard },
  { to: "/live-transactions", label: "Live Transactions", icon: Activity },
  { to: "/fraud-alerts", label: "Fraud Alerts", icon: ShieldAlert },
  { to: "/investigation", label: "Investigation", icon: Search },
  { to: "/fraud-map", label: "Fraud Map", icon: Map },
  { to: "/analytics", label: "Analytics", icon: ChartNoAxesCombined },
  { to: "/ml-model", label: "ML Model", icon: BrainCircuit },
  { to: "/settings", label: "Settings", icon: Settings },
] as const;

function Clock() {
  const now = new Date();
  return (
    <span className="num hidden text-xs text-muted-foreground md:inline">
      {now.toLocaleDateString("en-IN", { day: "2-digit", month: "short", year: "numeric" })} ·{" "}
      {now.toLocaleTimeString("en-IN", { hour: "2-digit", minute: "2-digit" })} IST
    </span>
  );
}

function Notifications() {
  const { notifications } = useLiveState();
  const [open, setOpen] = useState(false);
  return (
    <div className="relative">
      <button
        onClick={() => setOpen((o) => !o)}
        aria-label="Notifications"
        className="relative rounded-lg border border-border bg-card p-2 text-muted-foreground transition-colors hover:text-foreground"
      >
        <Bell className="h-4 w-4" />
        {notifications.length > 0 ? (
          <span className="num absolute -right-1.5 -top-1.5 flex h-4 min-w-4 items-center justify-center rounded-full bg-critical px-1 text-[10px] font-bold text-critical-foreground">
            {notifications.length}
          </span>
        ) : null}
      </button>
      {open ? (
        <div className="absolute right-0 z-50 mt-2 w-80 overflow-hidden rounded-xl border border-border bg-card shadow-sm">
          <div className="border-b border-border px-4 py-3 text-xs font-semibold text-foreground">
            Fraud notifications
          </div>
          <ul className="max-h-80 overflow-y-auto">
            {notifications.length === 0 ? (
              <li className="px-4 py-6 text-center text-xs text-muted-foreground">
                No new notifications
              </li>
            ) : null}
            {notifications.map((n) => (
              <li key={n.id} className="border-b border-border last:border-0">
                <Link
                  to="/investigation"
                  search={{ tx: n.transactionId }}
                  onClick={() => setOpen(false)}
                  className="block px-4 py-3 transition-colors hover:bg-muted/60"
                >
                  <p className="text-xs font-semibold text-critical">{n.title}</p>
                  <p className="num mt-0.5 text-sm text-foreground">{n.body}</p>
                  <p className="num mt-0.5 text-[11px] text-muted-foreground">
                    Risk Score: {n.riskScore} · {n.time}
                  </p>
                </Link>
              </li>
            ))}
          </ul>
        </div>
      ) : null}
    </div>
  );
}

export function AppShell({
  title,
  subtitle,
  children,
}: {
  title: string;
  subtitle: string;
  children: ReactNode;
}) {
  const pathname = useRouterState({ select: (s) => s.location.pathname });

  return (
    <div className="flex min-h-screen bg-background">
      <aside className="sticky top-0 hidden h-screen w-60 shrink-0 flex-col border-r border-border bg-card lg:flex">
        <div className="flex items-center gap-2.5 border-b border-border px-5 py-4">
          <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary text-primary-foreground">
            <ShieldCheck className="h-4 w-4" />
          </span>
          <div>
            <p className="text-sm font-semibold leading-tight text-foreground">SentinelPay</p>
            <p className="text-[11px] leading-tight text-muted-foreground">Fraud Intelligence</p>
          </div>
        </div>
        <nav className="flex-1 space-y-0.5 p-3">
          {NAV.map((item) => {
            const active = pathname === item.to;
            return (
              <Link
                key={item.to}
                to={item.to}
                className={cn(
                  "flex items-center gap-2.5 rounded-lg px-3 py-2 text-sm transition-colors",
                  active
                    ? "bg-primary text-primary-foreground"
                    : "text-muted-foreground hover:bg-muted hover:text-foreground",
                )}
              >
                <item.icon className="h-4 w-4" />
                {item.label}
              </Link>
            );
          })}
        </nav>
        <div className="m-3 rounded-lg border border-border p-3">
          <div className="flex items-center gap-2">
            <span className="h-1.5 w-1.5 rounded-full bg-success" />
            <p className="text-xs font-medium text-foreground">Detection engine online</p>
          </div>
          <p className="mt-1 text-[11px] text-muted-foreground">
            XGBoost + Isolation Forest · v2.4.1
          </p>
        </div>
      </aside>

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="sticky top-0 z-40 flex flex-wrap items-center justify-between gap-3 border-b border-border bg-card/95 px-5 py-4 backdrop-blur">
          <div className="min-w-0">
            <h1 className="truncate text-lg font-semibold text-foreground">{title}</h1>
            <p className="truncate text-xs text-muted-foreground">{subtitle}</p>
          </div>
          <div className="flex items-center gap-3">
            <LiveDot />
            <Clock />
            <Notifications />
            <Link
              to="/settings"
              className="flex items-center gap-2 rounded-lg border border-border bg-card px-2 py-1.5"
            >
              <span className="flex h-6 w-6 items-center justify-center rounded-full bg-muted text-muted-foreground">
                <UserRound className="h-3.5 w-3.5" />
              </span>
              <span className="hidden text-xs font-medium text-foreground sm:inline">
                A. Nair · Analyst
              </span>
            </Link>
          </div>
        </header>

        <div className="lg:hidden">
          <nav className="flex gap-1 overflow-x-auto border-b border-border bg-card px-3 py-2">
            {NAV.map((item) => (
              <Link
                key={item.to}
                to={item.to}
                className={cn(
                  "whitespace-nowrap rounded-md px-3 py-1.5 text-xs",
                  pathname === item.to
                    ? "bg-primary text-primary-foreground"
                    : "text-muted-foreground",
                )}
              >
                {item.label}
              </Link>
            ))}
          </nav>
        </div>

        <main className="flex-1 space-y-4 p-4 lg:p-6">{children}</main>
      </div>
    </div>
  );
}
