import { useSyncExternalStore } from "react";
import { subscribeToTransactions } from "./api";
import { SEED_TRANSACTIONS } from "./mock";
import type { Transaction } from "./types";

export interface LiveNotification {
  id: string;
  title: string;
  body: string;
  riskScore: number;
  transactionId: string;
  time: string;
  severity: "CRITICAL" | "HIGH" | "MEDIUM";
}

export interface LiveState {
  transactions: Transaction[];
  notifications: LiveNotification[];
  monitored: number;
  suspicious: number;
  fraud: number;
  blocked: number;
  preventedLoss: number;
  streaming: boolean;
}

const initial: LiveState = {
  transactions: SEED_TRANSACTIONS.slice().reverse(),
  notifications: [
    {
      id: "N-1",
      title: "Critical fraud detected",
      body: "TXN-84922 — ₹42,000",
      riskScore: 94,
      transactionId: "TXN-84922",
      time: "10:42:36",
      severity: "CRITICAL",
    },
  ],
  monitored: 12842,
  suspicious: 127,
  fraud: 34,
  blocked: 18,
  preventedLoss: 2438000,
  streaming: true,
};

let state: LiveState = initial;
const listeners = new Set<() => void>();

function emit(next: LiveState) {
  state = next;
  listeners.forEach((l) => l());
}

export function pushTransaction(tx: Transaction) {
  const isSuspicious = tx.status === "SUSPICIOUS" || tx.status === "REVIEW";
  const isFraud = tx.status === "BLOCKED";
  const notifications = isFraud
    ? [
        {
          id: `N-${tx.id}`,
          title: "Critical fraud detected",
          body: `${tx.id} — ₹${tx.amount.toLocaleString("en-IN")}`,
          riskScore: tx.riskScore,
          transactionId: tx.id,
          time: tx.time,
          severity: "CRITICAL" as const,
        },
        ...state.notifications,
      ].slice(0, 12)
    : state.notifications;

  emit({
    ...state,
    transactions: [tx, ...state.transactions].slice(0, 120),
    notifications,
    monitored: state.monitored + 1,
    suspicious: state.suspicious + (isSuspicious ? 1 : 0),
    fraud: state.fraud + (isFraud ? 1 : 0),
    blocked: state.blocked + (isFraud ? 1 : 0),
    preventedLoss: state.preventedLoss + (isFraud ? tx.amount : 0),
  });
}

export function setStreaming(streaming: boolean) {
  emit({ ...state, streaming });
}

let started = false;
function ensureStream() {
  if (started || typeof window === "undefined") return;
  started = true;
  subscribeToTransactions((tx) => {
    if (state.streaming) pushTransaction(tx);
  });
}

function subscribe(listener: () => void) {
  ensureStream();
  listeners.add(listener);
  return () => listeners.delete(listener);
}

const getSnapshot = () => state;

export function useLiveState(): LiveState {
  return useSyncExternalStore(subscribe, getSnapshot, () => initial);
}
