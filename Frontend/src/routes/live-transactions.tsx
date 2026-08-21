import { createFileRoute } from "@tanstack/react-router";
import { Activity, ShieldAlert, ShieldX, Timer } from "lucide-react";
import { AppShell } from "@/components/fraud/AppShell";
import { KpiCard } from "@/components/fraud/KpiCard";
import { TransactionTable } from "@/components/fraud/TransactionTable";
import { useLiveState } from "@/lib/fraud/live-store";

export const Route = createFileRoute("/live-transactions")({
  head: () => ({
    meta: [
      { title: "Live Transactions | SentinelPay" },
      {
        name: "description",
        content: "Streaming payment events scored in real time with risk, device and location context.",
      },
      { property: "og:title", content: "Live Transactions | SentinelPay" },
      { property: "og:description", content: "Real-time payment transaction stream and risk scoring." },
    ],
  }),
  component: LiveTransactions,
});

function LiveTransactions() {
  const live = useLiveState();
  const lastMinute = live.transactions.filter((t) => Date.now() - t.timestamp < 60000).length;

  return (
    <AppShell
      title="Live Transactions"
      subtitle="Every payment event scored the moment it is authorised"
    >
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <KpiCard
          label="Events In Session"
          value={live.transactions.length.toString()}
          support="Streaming from the decision engine"
          icon={Activity}
        />
        <KpiCard
          label="Events Last Minute"
          value={lastMinute.toString()}
          support="Throughput in the current window"
          icon={Timer}
          tone="info"
        />
        <KpiCard
          label="Flagged For Review"
          value={live.transactions.filter((t) => t.status === "REVIEW" || t.status === "SUSPICIOUS").length.toString()}
          support="Awaiting analyst decision"
          icon={ShieldAlert}
          tone="warning"
        />
        <KpiCard
          label="Auto-Blocked"
          value={live.transactions.filter((t) => t.status === "BLOCKED").length.toString()}
          support="Stopped before settlement"
          icon={ShieldX}
          tone="critical"
        />
      </div>
      <TransactionTable
        transactions={live.transactions}
        title="Transaction Stream"
        subtitle="Filter by risk, status, time window and location"
      />
    </AppShell>
  );
}
