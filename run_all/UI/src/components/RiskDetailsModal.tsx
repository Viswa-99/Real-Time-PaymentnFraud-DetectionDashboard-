import React from "react";
import { type Txn } from "@/lib/fraud-data";

interface RiskDetailsModalProps {
  txn: Txn | null;
  onClose: () => void;
}

export const RiskDetailsModal: React.FC<RiskDetailsModalProps> = ({ txn, onClose }) => {
  if (!txn) return null;

  const isBlocked = txn.status === "BLOCKED" || txn.risk_probability >= 0.86;
  const isReview = txn.status === "UNDER_REVIEW" || (txn.risk_probability >= 0.30 && txn.risk_probability < 0.86);

  // Generate fallback reason items if backend reasons array was not present
  const reasonsList = txn.reasons && txn.reasons.length > 0 ? txn.reasons : [
    {
      title: String(txn.anomaly_type || "Behavioral Risk Detected").replace(/_/g, " "),
      detail: `Model risk probability is ${(txn.risk_probability * 100).toFixed(2)}%, exceeding the baseline decision threshold.`
    },
    {
      title: "Layer 1 Anomaly Score Trigger",
      detail: `Isolation Forest anomaly score is ${txn.layer1_anomaly_score.toFixed(4)}, indicating significant structural baseline deviation.`
    }
  ];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4 animate-in fade-in duration-200">
      <div className="relative w-full max-w-2xl overflow-hidden rounded-2xl border border-border bg-card shadow-2xl">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-border p-5 bg-muted/30">
          <div>
            <span className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
              UPI Threat Investigation
            </span>
            <h2 className="text-xl font-bold text-foreground flex items-center gap-2 mt-0.5">
              <span>{txn.transaction_id}</span>
            </h2>
          </div>
          <button
            onClick={onClose}
            className="rounded-lg p-2 text-muted-foreground hover:bg-accent hover:text-foreground transition-colors"
          >
            ✕
          </button>
        </div>

        <div className="max-h-[80vh] overflow-y-auto p-6 space-y-6">
          {/* Status & Risk Banner */}
          <div
            className={`rounded-xl border p-4 flex flex-wrap items-center justify-between gap-4 ${
              isBlocked
                ? "bg-red-500/10 border-red-500/30 text-red-400"
                : isReview
                ? "bg-amber-500/10 border-amber-500/30 text-amber-400"
                : "bg-green-500/10 border-green-500/30 text-green-400"
            }`}
          >
            <div>
              <div className="text-xs font-bold uppercase tracking-wide opacity-80">
                Model Decision Status
              </div>
              <div className="text-lg font-extrabold flex items-center gap-2 mt-0.5">
                <span>{isBlocked ? "🚨 AUTO-BLOCKED (ANOMALY DETECTED)" : isReview ? "⚠️ QUEUED FOR ANALYST REVIEW" : "✅ APPROVED (NORMAL)"}</span>
              </div>
            </div>
            <div className="text-right">
              <div className="text-2xl font-black tabular-nums">
                {txn.risk_score.toFixed(2)}%
              </div>
              <div className="text-xs opacity-80 font-mono">
                p = {txn.risk_probability.toFixed(4)}
              </div>
            </div>
          </div>

          {/* Layer 1 & Layer 2 Model Diagnostics */}
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div className="rounded-xl border border-border bg-background p-4">
              <div className="text-xs font-medium text-muted-foreground uppercase">Layer 1 Isolation Forest</div>
              <div className="text-lg font-mono font-bold text-foreground mt-1 tabular-nums">
                {txn.layer1_anomaly_score.toFixed(4)}
              </div>
              <div className="text-xs text-muted-foreground mt-0.5">Baseline threshold: 0.5136</div>
            </div>
            <div className="rounded-xl border border-border bg-background p-4">
              <div className="text-xs font-medium text-muted-foreground uppercase">Layer 2 XGBoost Model</div>
              <div className="text-lg font-mono font-bold text-foreground mt-1 tabular-nums">
                {(txn.risk_probability * 100).toFixed(2)}%
              </div>
              <div className="text-xs text-muted-foreground mt-0.5">Decision threshold: 86.00%</div>
            </div>
          </div>

          {/* HUMAN-READABLE RISK REASONS */}
          <div className="rounded-xl border border-border bg-background p-5">
            <h3 className="text-sm font-bold text-foreground uppercase tracking-wide mb-3 flex items-center gap-2">
              <span>📋 Human-Readable Risk Explanations (Reason Engine)</span>
            </h3>
            <div className="space-y-3">
              {reasonsList.map((reason, idx) => (
                <div key={idx} className="flex items-start gap-3 p-3 rounded-lg bg-accent/40 border border-border/50">
                  <span className="flex-none mt-0.5 text-base">🔴</span>
                  <div>
                    <div className="text-sm font-bold text-foreground">
                      {reason.title}
                    </div>
                    <div className="text-xs text-muted-foreground mt-0.5 leading-relaxed">
                      {reason.detail}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Transaction Metadata Grid */}
          <div className="rounded-xl border border-border bg-background p-5 space-y-3 text-sm">
            <h3 className="text-sm font-bold text-foreground uppercase tracking-wide border-b border-border pb-2">
              Transaction Details
            </h3>
            <div className="grid grid-cols-2 gap-x-6 gap-y-2 font-mono text-xs">
              <div className="flex justify-between">
                <span className="text-muted-foreground">Amount:</span>
                <span className="font-bold text-foreground">₹{txn.amount.toLocaleString("en-IN", { minimumFractionDigits: 2 })}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Sender User ID:</span>
                <span className="text-foreground">{txn.user_id}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Receiver / Merchant:</span>
                <span className="text-foreground">{txn.receiver_id || txn.merchant_id || "N/A"}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Location Region:</span>
                <span className="text-foreground">{txn.location}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Device Type:</span>
                <span className="text-foreground">{txn.device}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Timestamp:</span>
                <span className="text-foreground">{new Date(txn.timestamp).toLocaleString()}</span>
              </div>
            </div>
          </div>
        </div>

        {/* Footer Actions */}
        <div className="flex items-center justify-end gap-3 border-t border-border p-4 bg-muted/20">
          <button
            onClick={onClose}
            className="rounded-lg border border-border bg-background px-4 py-2 text-sm font-medium text-foreground hover:bg-accent transition-colors"
          >
            Close
          </button>
          {isBlocked && (
            <button
              onClick={onClose}
              className="rounded-lg bg-red-600 px-4 py-2 text-sm font-semibold text-white hover:bg-red-700 transition-colors"
            >
              Confirm Block Threat
            </button>
          )}
        </div>
      </div>
    </div>
  );
};
