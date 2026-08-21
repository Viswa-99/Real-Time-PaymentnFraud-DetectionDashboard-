import { createFileRoute } from "@tanstack/react-router";
import {
  Activity,
  BadgeIndianRupee,
  ShieldAlert,
  ShieldX,
  Sparkles,
} from "lucide-react";
import { AppShell } from "@/components/fraud/AppShell";
import { KpiCard } from "@/components/fraud/KpiCard";
import { TransactionActivity } from "@/components/fraud/TransactionActivity";
import { RiskFactorsPanel, RiskScorePanel } from "@/components/fraud/RiskPanel";
import { TransactionTable } from "@/components/fraud/TransactionTable";
import { FraudDetectionAlert } from "@/components/fraud/FraudDetectionAlert";
import { LocationAnomalyCard } from "@/components/fraud/LocationAnomaly";
import { BehaviorCard } from "@/components/fraud/BehaviorCard";
import { RecentAlerts } from "@/components/fraud/RecentAlerts";
import { DetectionFlow, ModelInsights } from "@/components/fraud/ModelInsights";
import { useLiveState } from "@/lib/fraud/live-store";
import { formatLakh } from "@/lib/fraud/mock";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "Fraud Detection Dashboard | SentinelPay" },
      {
        name: "description",
        content:
          "Real-time payment fraud monitoring with AI risk scoring, anomaly detection and investigation workflows.",
      },
      { property: "og:title", content: "Fraud Detection Dashboard | SentinelPay" },
      {
        property: "og:description",
        content: "Real-time monitoring and AI-powered payment risk intelligence.",
      },
    ],
  }),
  component: Dashboard,
});

function Dashboard() {
  const live = useLiveState();

  return (
    <AppShell
      title="Fraud Detection Dashboard"
      subtitle="Real-time monitoring and AI-powered payment risk intelligence"
    >
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-5">
        <KpiCard
          label="Transactions Monitored"
          value={live.monitored.toLocaleString("en-IN")}
          support="+8.4% from yesterday"
          icon={Activity}
        />
        <KpiCard
          label="Suspicious Transactions"
          value={live.suspicious.toLocaleString("en-IN")}
          support="+14% from last week"
          icon={ShieldAlert}
          tone="warning"
        />
        <KpiCard
          label="Fraud Detected"
          value={live.fraud.toLocaleString("en-IN")}
          support={`${live.blocked} blocked automatically`}
          icon={ShieldX}
          tone="critical"
        />
        <KpiCard
          label="Prevented Loss"
          value={formatLakh(live.preventedLoss)}
          support="Estimated fraudulent value prevented"
          icon={BadgeIndianRupee}
          tone="success"
        />
        <KpiCard
          label="AI Detection Rate"
          value="92.4%"
          support="Model performance · FPR 4.3%"
          icon={Sparkles}
          tone="info"
        />
      </div>

      <div className="grid gap-4 xl:grid-cols-3">
        <div className="space-y-4 xl:col-span-2">
          <TransactionActivity />
          <div className="grid gap-4 lg:grid-cols-2">
            <LocationAnomalyCard />
            <BehaviorCard />
          </div>
        </div>
        <div className="space-y-4">
          <RiskScorePanel />
          <RiskFactorsPanel />
        </div>
      </div>

      <div className="grid items-start gap-4 xl:grid-cols-3">
        <div className="xl:col-span-2">
          <TransactionTable transactions={live.transactions} compact />
        </div>
        <FraudDetectionAlert />
      </div>

      <DetectionFlow />

      <div className="grid gap-4 xl:grid-cols-2">
        <RecentAlerts limit={4} />
        <ModelInsights />
      </div>
    </AppShell>
  );
}
