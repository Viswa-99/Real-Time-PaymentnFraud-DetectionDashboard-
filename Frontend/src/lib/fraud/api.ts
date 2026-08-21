/**
 * API-ready service layer.
 *
 * Every function below mirrors a planned FastAPI endpoint. Today they resolve
 * mock data; swapping `USE_MOCK` to false (and setting VITE_API_BASE_URL)
 * routes the same calls to the real backend without touching any component.
 *
 *   GET  /transactions
 *   GET  /transactions/{id}
 *   GET  /alerts
 *   GET  /alerts/{id}
 *   GET  /risk/{transaction_id}
 *   GET  /analytics
 *   GET  /model/metrics
 *   GET  /users/{id}/transactions
 *   WS   /ws/transactions
 */
import {
  ACTIVITY,
  ALERTS,
  DEMO_BEHAVIOR,
  DEMO_LOCATION_EVENT,
  DEMO_RISK,
  LOCATION_RISK,
  MODEL_METRICS,
  SEED_TRANSACTIONS,
  makeTransaction,
} from "./mock";
import type {
  ActivityPoint,
  FraudAlert,
  LocationEvent,
  LocationRisk,
  ModelMetrics,
  RiskScore,
  Transaction,
  UserBehavior,
} from "./types";

export const API_BASE_URL = import.meta.env["VITE_API_BASE_URL"] ?? "http://localhost:8000";
export const USE_MOCK = true;

async function request<T>(path: string, fallback: T): Promise<T> {
  if (USE_MOCK) return Promise.resolve(fallback);
  const res = await fetch(`${API_BASE_URL}${path}`);
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
  return (await res.json()) as T;
}

export const fraudApi = {
  getTransactions: () => request<Transaction[]>("/transactions", SEED_TRANSACTIONS),
  getTransaction: (id: string) =>
    request<Transaction | undefined>(
      `/transactions/${id}`,
      SEED_TRANSACTIONS.find((t) => t.id === id),
    ),
  getAlerts: () => request<FraudAlert[]>("/alerts", ALERTS),
  getAlert: (id: string) =>
    request<FraudAlert | undefined>(`/alerts/${id}`, ALERTS.find((a) => a.id === id)),
  getRisk: (transactionId: string) => request<RiskScore>(`/risk/${transactionId}`, DEMO_RISK),
  getAnalytics: () =>
    request<{ activity: typeof ACTIVITY; locations: LocationRisk[] }>("/analytics", {
      activity: ACTIVITY,
      locations: LOCATION_RISK,
    }),
  getModelMetrics: () => request<ModelMetrics>("/model/metrics", MODEL_METRICS),
  getUserBehavior: (userId: string) =>
    request<UserBehavior>(`/users/${userId}/behavior`, DEMO_BEHAVIOR),
  getUserTransactions: (userId: string) =>
    request<Transaction[]>(
      `/users/${userId}/transactions`,
      SEED_TRANSACTIONS.filter((t) => t.userId === userId),
    ),
  getLocationEvent: (transactionId: string) =>
    request<LocationEvent>(`/risk/${transactionId}/location`, DEMO_LOCATION_EVENT),
};

export type { ActivityPoint };

/**
 * Live stream subscriber. Connects to the Transaction Stimulation Bot's WebSocket stream 
 * at ws://localhost:8080 with seamless fallback to high-speed simulation.
 */
export function subscribeToTransactions(onTransaction: (tx: Transaction) => void) {
  let cancelled = false;
  let timer: ReturnType<typeof setTimeout>;
  let socket: WebSocket | null = null;

  const tryConnectWs = () => {
    try {
      const wsUrl = import.meta.env["VITE_WS_SIMULATOR_URL"] ?? "ws://localhost:8080";
      socket = new WebSocket(wsUrl);

      socket.onmessage = (event) => {
        if (cancelled) return;
        try {
          const data = JSON.parse(event.data);
          const txn: Transaction = data.transaction || data;
          if (txn && txn.id) {
            onTransaction(txn);
          }
        } catch {
          // ignore malformed frame
        }
      };

      socket.onerror = () => {
        // Fallback to internal generator if WS fails to connect
        if (!cancelled && !timer) startFallbackTimer();
      };

      socket.onclose = () => {
        if (!cancelled) {
          // Retry connection after 3s
          setTimeout(tryConnectWs, 3000);
        }
      };
    } catch {
      startFallbackTimer();
    }
  };

  const startFallbackTimer = () => {
    const tick = () => {
      if (cancelled) return;
      onTransaction(makeTransaction());
      timer = setTimeout(tick, 1000);
    };
    timer = setTimeout(tick, 1000);
  };

  tryConnectWs();

  return () => {
    cancelled = true;
    if (timer) clearTimeout(timer);
    if (socket) {
      socket.onclose = null;
      socket.close();
    }
  };
}

