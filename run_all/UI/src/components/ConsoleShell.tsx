import { Link } from "@tanstack/react-router";
import {
  Activity,
  BarChart3,
  LayoutDashboard,
  ShieldAlert,
  Radar,
  type LucideIcon,
} from "lucide-react";
import type { ReactNode } from "react";

const NAV: { to: string; label: string; icon: LucideIcon }[] = [
  { to: "/", label: "Dashboard", icon: LayoutDashboard },
  { to: "/alerts", label: "Alerts", icon: ShieldAlert },
  { to: "/analysis", label: "Model Analysis", icon: BarChart3 },
];

export function ConsoleShell({
  title,
  subtitle,
  actions,
  children,
}: {
  title: string;
  subtitle: string;
  actions?: ReactNode;
  children: ReactNode;
}) {
  return (
    <div className="min-h-screen bg-surface text-foreground">
      <header className="sticky top-0 z-20 flex h-14 items-center gap-3 border-b border-border bg-background px-5">
        <span className="flex size-8 items-center justify-center rounded-lg bg-primary text-primary-foreground">
          <Radar className="size-4" />
        </span>
        <span className="text-sm font-semibold tracking-tight">Payments Fraud Detection</span>
        <span className="ml-auto flex items-center gap-2 rounded-full border border-border px-3 py-1 text-xs text-muted-foreground">
          <Activity className="size-3.5 text-risk-low" />
          Layer 1 + Layer 2 pipeline
        </span>
      </header>

      <div className="flex">
        <aside className="sticky top-14 hidden h-[calc(100vh-3.5rem)] w-56 shrink-0 border-r border-border bg-background p-3 md:block">
          <nav className="flex flex-col gap-1">
            {NAV.map(({ to, label, icon: Icon }) => (
              <Link
                key={to}
                to={to}
                activeOptions={{ exact: to === "/" }}
                activeProps={{ className: "bg-accent font-medium text-foreground" }}
                className="flex items-center gap-2.5 rounded-lg px-3 py-2 text-sm text-muted-foreground transition-colors hover:bg-accent hover:text-foreground"
              >
                <Icon className="size-4" />
                {label}
              </Link>
            ))}
          </nav>
        </aside>

        <main className="min-w-0 flex-1 p-5 lg:p-7">
          <div className="mb-6 flex flex-wrap items-end justify-between gap-4">
            <div>
              <h1 className="text-2xl font-semibold tracking-tight lg:text-3xl">{title}</h1>
              <p className="mt-1 text-sm text-muted-foreground">{subtitle}</p>
            </div>
            {actions}
          </div>
          {children}
        </main>
      </div>
    </div>
  );
}
