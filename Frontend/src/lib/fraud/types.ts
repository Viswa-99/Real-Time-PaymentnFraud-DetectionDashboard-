export type RiskLevel = "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
export type TxStatus = "SAFE" | "REVIEW" | "SUSPICIOUS" | "BLOCKED";

export interface Transaction {
  id: string;
  time: string;
  timestamp: number;
  userId: string;
  merchant: string;
  amount: number;
  location: string;
  device: string;
  deviceKnown: boolean;
  ip: string;
  paymentMethod: string;
  riskScore: number;
  status: TxStatus;
  reason?: string | undefined;
}

export interface RiskFactor {
  label: string;
  weight: number;
  detail: string;
}

export interface RiskScore {
  transactionId: string;
  score: number;
  probability: number;
  level: RiskLevel;
  mlProbability: number;
  anomalyScore: number;
  ruleScore: number;
  factors: RiskFactor[];
}

export interface FraudAlert {
  id: string;
  type: string;
  severity: RiskLevel;
  transactionId: string;
  userId: string;
  amount: number;
  detectedAt: string;
  ago: string;
  reason: string;
  reasons: string[];
  status: "Open" | "Under Review" | "Escalated" | "Resolved";
  riskScore: number;
  probability: number;
  recommendedAction: string;
}

export interface UserBehavior {
  userId: string;
  averageTransaction: number;
  currentTransaction: number;
  deviation: number;
  transactionsToday: number;
  normalDailyAverage: number;
  transactionsLast10Min: number;
  normalVelocity: string;
  status: string;
}

export interface LocationEvent {
  transactionId: string;
  previousLocation: string;
  currentLocation: string;
  distanceKm: number;
  minutesApart: number;
  requiredSpeedKmh: number;
  impossibleTravel: boolean;
}

export interface ModelMetrics {
  model: string;
  anomalyModel: string;
  accuracy: number;
  precision: number;
  recall: number;
  f1: number;
  falsePositiveRate: number;
  signals: { name: string; strength: number }[];
}

export interface ActivityPoint {
  label: string;
  avgAmount: number;
  volume: number;
  suspicious: number;
}

export interface LocationRisk {
  city: string;
  lat: number;
  lng: number;
  transactions: number;
  suspicious: number;
}
