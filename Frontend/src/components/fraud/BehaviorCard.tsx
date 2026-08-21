import { Gauge } from "lucide-react";
import { DEMO_BEHAVIOR, formatINR } from "@/lib/fraud/mock";
import { MeterBar, Panel, PanelHeader } from "./primitives";

export function BehaviorCard() {
  const b = DEMO_BEHAVIOR;
  return (
    <Panel>
      <PanelHeader
        title="User Transaction Behavior"
        subtitle={`Baseline deviation for ${b.userId}`}
        icon={<Gauge className="h-4 w-4" />}
      />
      <div className="space-y-4 px-5 py-4">
        <div className="grid grid-cols-2 gap-3">
          <Stat label="Average Transaction" value={formatINR(b.averageTransaction)} />
          <Stat label="Current Transaction" value={formatINR(b.currentTransaction)} critical />
        </div>
        <div>
          <div className="flex items-center justify-between text-xs">
            <span className="text-muted-foreground">Amount deviation</span>
            <span className="num font-semibold text-critical">{b.deviation}×</span>
          </div>
          <div className="mt-1.5">
            <MeterBar value={95} tone="critical" />
          </div>
        </div>
        <div>
          <div className="flex items-center justify-between text-xs">
            <span className="text-muted-foreground">
              Transactions today ({b.transactionsToday}) vs normal ({b.normalDailyAverage})
            </span>
            <span className="num font-semibold text-warning-foreground">3.6×</span>
          </div>
          <div className="mt-1.5">
            <MeterBar value={82} tone="warning" />
          </div>
        </div>
        <div>
          <div className="flex items-center justify-between text-xs">
            <span className="text-muted-foreground">
              Last 10 min ({b.transactionsLast10Min}) vs normal ({b.normalVelocity})
            </span>
            <span className="num font-semibold text-critical">6×</span>
          </div>
          <div className="mt-1.5">
            <MeterBar value={90} tone="critical" />
          </div>
        </div>
        <div className="flex items-center justify-between rounded-lg border border-critical/30 bg-critical-soft px-3 py-2">
          <span className="text-xs text-critical/90">Behavior status</span>
          <span className="text-xs font-semibold text-critical">{b.status}</span>
        </div>
      </div>
    </Panel>
  );
}

function Stat({ label, value, critical }: { label: string; value: string; critical?: boolean }) {
  return (
    <div className="rounded-lg border border-border p-3">
      <p className="text-[11px] text-muted-foreground">{label}</p>
      <p
        className={`num mt-1 text-lg font-semibold ${critical ? "text-critical" : "text-foreground"}`}
      >
        {value}
      </p>
    </div>
  );
}
