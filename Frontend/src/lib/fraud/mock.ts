import type {
  ActivityPoint,
  FraudAlert,
  LocationEvent,
  LocationRisk,
  ModelMetrics,
  RiskScore,
  Transaction,
  TxStatus,
  UserBehavior,
} from "./types";

export const CITIES = ["Hyderabad", "Bangalore", "Chennai", "Mumbai", "Delhi", "Pune", "Kolkata"];
const MERCHANTS = [
  "Swiggy Foods",
  "Amazon Pay",
  "IRCTC",
  "Reliance Retail",
  "Flipkart",
  "BigBasket",
  "Croma Electronics",
  "Apollo Pharmacy",
];

export const formatINR = (n: number) =>
  "₹" + n.toLocaleString("en-IN", { maximumFractionDigits: 0 });

export function formatLakh(n: number) {
  if (n >= 10000000) return `₹${(n / 10000000).toFixed(2)}Cr`;
  if (n >= 100000) return `₹${(n / 100000).toFixed(2)}L`;
  return formatINR(n);
}

export function statusFromScore(score: number): TxStatus {
  if (score >= 85) return "BLOCKED";
  if (score >= 70) return "SUSPICIOUS";
  if (score >= 45) return "REVIEW";
  return "SAFE";
}

export function levelFromScore(score: number) {
  if (score >= 85) return "CRITICAL" as const;
  if (score >= 70) return "HIGH" as const;
  if (score >= 45) return "MEDIUM" as const;
  return "LOW" as const;
}

const pick = <T,>(a: T[]): T => a[Math.floor(Math.random() * a.length)] as T;
const pad = (n: number) => String(n).padStart(2, "0");

export function clockFrom(ts: number) {
  const d = new Date(ts);
  return `${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`;
}

let txCounter = 84923;

export function makeTransaction(opts?: Partial<Transaction>): Transaction {
  txCounter += 1;
  const suspicious = Math.random() < 0.14;
  const critical = Math.random() < 0.05;
  const amount = critical
    ? 25000 + Math.floor(Math.random() * 30000)
    : suspicious
      ? 8000 + Math.floor(Math.random() * 12000)
      : 300 + Math.floor(Math.random() * 4200);
  const deviceKnown = critical ? false : Math.random() > 0.25;
  const score = critical
    ? 86 + Math.floor(Math.random() * 12)
    : suspicious
      ? 55 + Math.floor(Math.random() * 25)
      : 5 + Math.floor(Math.random() * 35);
  const ts = Date.now();
  return {
    id: `TXN-${txCounter}`,
    timestamp: ts,
    time: clockFrom(ts),
    userId: `USR-${1000 + Math.floor(Math.random() * 9000)}`,
    merchant: pick(MERCHANTS),
    amount,
    location: pick(CITIES),
    device: deviceKnown ? "Known Device" : "New Device",
    deviceKnown,
    ip: `49.${Math.floor(Math.random() * 200)}.${Math.floor(Math.random() * 250)}.${Math.floor(Math.random() * 250)}`,
    paymentMethod: pick(["UPI", "Credit Card", "Debit Card", "Net Banking", "Wallet"]),
    riskScore: score,
    status: statusFromScore(score),
    reason: critical
      ? "High value from unrecognized device"
      : suspicious
        ? "Amount deviates from user baseline"
        : undefined,
    ...opts,
  };
}

export const DEMO_FRAUD_TX: Transaction = {
  id: "TXN-84922",
  timestamp: Date.now(),
  time: "10:42:36",
  userId: "USR-1024",
  merchant: "Croma Electronics",
  amount: 42000,
  location: "Chennai",
  device: "New Device",
  deviceKnown: false,
  ip: "103.211.19.84",
  paymentMethod: "Credit Card",
  riskScore: 94,
  status: "BLOCKED",
  reason: "Impossible travel + amount deviation",
};

export const SEED_TRANSACTIONS: Transaction[] = [
  {
    id: "TXN-84921",
    timestamp: Date.now() - 5000,
    time: "10:42:31",
    userId: "USR-1024",
    merchant: "Swiggy Foods",
    amount: 2400,
    location: "Hyderabad",
    device: "Known Device",
    deviceKnown: true,
    ip: "49.205.12.4",
    paymentMethod: "UPI",
    riskScore: 18,
    status: "SAFE",
  },
  DEMO_FRAUD_TX,
  {
    id: "TXN-84923",
    timestamp: Date.now() - 1000,
    time: "10:42:41",
    userId: "USR-3192",
    merchant: "Amazon Pay",
    amount: 8500,
    location: "Bangalore",
    device: "Known Device",
    deviceKnown: true,
    ip: "49.37.140.9",
    paymentMethod: "Debit Card",
    riskScore: 63,
    status: "REVIEW",
    reason: "Above average ticket size",
  },
];

export const DEMO_RISK: RiskScore = {
  transactionId: "TXN-84922",
  score: 87,
  probability: 91.7,
  level: "HIGH",
  mlProbability: 94.2,
  anomalyScore: 91,
  ruleScore: 88,
  factors: [
    { label: "Transaction Amount", weight: 92, detail: "11.4× user's average" },
    { label: "Location Anomaly", weight: 88, detail: "Multiple locations detected" },
    { label: "Device Risk", weight: 76, detail: "New/unrecognized device" },
    { label: "Transaction Velocity", weight: 84, detail: "9 transactions in 2 minutes" },
    { label: "Time Anomaly", weight: 62, detail: "Unusual transaction time" },
  ],
};

export const FRAUD_REASONS = [
  "Transaction amount is 11.4× higher than the user's average",
  "Transaction occurred from a new/unrecognized device",
  "Previous transaction was detected in Hyderabad",
  "Current transaction occurred in Chennai",
  "Location change occurred within 7 minutes",
  "Transaction velocity exceeded the user's normal behavior",
  "Transaction occurred outside the user's normal transaction period",
];

export const DEMO_LOCATION_EVENT: LocationEvent = {
  transactionId: "TXN-84922",
  previousLocation: "Hyderabad",
  currentLocation: "Chennai",
  distanceKm: 510,
  minutesApart: 7,
  requiredSpeedKmh: 4370,
  impossibleTravel: true,
};

export const DEMO_BEHAVIOR: UserBehavior = {
  userId: "USR-1024",
  averageTransaction: 3200,
  currentTransaction: 42000,
  deviation: 13.1,
  transactionsToday: 18,
  normalDailyAverage: 5,
  transactionsLast10Min: 9,
  normalVelocity: "1–2",
  status: "Highly Anomalous",
};

export const ALERTS: FraudAlert[] = [
  {
    id: "FA-10291",
    type: "Impossible Travel",
    severity: "CRITICAL",
    transactionId: "TXN-84922",
    userId: "USR-1024",
    amount: 42000,
    detectedAt: "10:42:36",
    ago: "2 minutes ago",
    reason: "Hyderabad → Chennai within 7 minutes",
    reasons: [
      "Amount is 13.1× above user average",
      "New device detected",
      "New IP address detected",
      "Impossible travel detected",
      "Velocity anomaly",
      "Unusual transaction time",
    ],
    status: "Open",
    riskScore: 94,
    probability: 96.2,
    recommendedAction: "Block transaction and initiate account verification.",
  },
  {
    id: "FA-10290",
    type: "Unusual Transaction Pattern",
    severity: "HIGH",
    transactionId: "TXN-84898",
    userId: "USR-7741",
    amount: 38500,
    detectedAt: "10:32:10",
    ago: "10 minutes ago",
    reason: "Multiple high-value transactions",
    reasons: [
      "4 high-value transactions within 6 minutes",
      "Amount 7.8× above user average",
      "Merchant category rarely used by this user",
    ],
    status: "Under Review",
    riskScore: 81,
    probability: 84.5,
    recommendedAction: "Hold transactions and request step-up authentication.",
  },
  {
    id: "FA-10289",
    type: "Impossible Travel",
    severity: "CRITICAL",
    transactionId: "TXN-84871",
    userId: "USR-2210",
    amount: 52000,
    detectedAt: "10:28:44",
    ago: "14 minutes ago",
    reason: "Hyderabad → Mumbai within 9 minutes",
    reasons: [
      "Geo-distance 710 km in 9 minutes",
      "Required travel speed 4,733 km/h",
      "Device fingerprint changed",
    ],
    status: "Escalated",
    riskScore: 93,
    probability: 95.1,
    recommendedAction: "Block card and freeze outbound payments pending verification.",
  },
  {
    id: "FA-10288",
    type: "New Device + High Value",
    severity: "HIGH",
    transactionId: "TXN-84840",
    userId: "USR-5583",
    amount: 27800,
    detectedAt: "10:21:02",
    ago: "21 minutes ago",
    reason: "Unrecognized device and abnormal amount",
    reasons: [
      "Device fingerprint not seen in last 180 days",
      "Amount 6.2× above user average",
      "IP geolocation mismatch with billing address",
    ],
    status: "Under Review",
    riskScore: 78,
    probability: 80.4,
    recommendedAction: "Send OTP verification before settlement.",
  },
  {
    id: "FA-10287",
    type: "Velocity Anomaly",
    severity: "MEDIUM",
    transactionId: "TXN-84802",
    userId: "USR-9134",
    amount: 14200,
    detectedAt: "10:10:19",
    ago: "32 minutes ago",
    reason: "8 transactions within 3 minutes",
    reasons: ["Velocity 4× above baseline", "Same merchant repeated charges"],
    status: "Open",
    riskScore: 58,
    probability: 61.3,
    recommendedAction: "Monitor account and throttle further attempts.",
  },
];

export const MODEL_METRICS: ModelMetrics = {
  model: "XGBoost Fraud Classifier",
  anomalyModel: "PyOD Isolation Forest",
  accuracy: 94.2,
  precision: 91.8,
  recall: 89.6,
  f1: 90.7,
  falsePositiveRate: 4.3,
  signals: [
    { name: "Transaction anomaly", strength: 92 },
    { name: "Location anomaly", strength: 88 },
    { name: "Device anomaly", strength: 76 },
    { name: "Velocity anomaly", strength: 84 },
    { name: "Behavioral deviation", strength: 81 },
    { name: "Merchant risk", strength: 54 },
    { name: "Time anomaly", strength: 62 },
  ],
};

export const ACTIVITY: Record<"day" | "week" | "month", ActivityPoint[]> = {
  day: [
    { label: "08:00", avgAmount: 1200, volume: 640, suspicious: 4 },
    { label: "10:00", avgAmount: 1850, volume: 910, suspicious: 7 },
    { label: "12:00", avgAmount: 1400, volume: 1180, suspicious: 6 },
    { label: "14:00", avgAmount: 2100, volume: 1020, suspicious: 11 },
    { label: "16:00", avgAmount: 1700, volume: 870, suspicious: 8 },
    { label: "18:00", avgAmount: 3900, volume: 1340, suspicious: 27 },
  ],
  week: [
    { label: "Mon", avgAmount: 1250, volume: 1720, suspicious: 12 },
    { label: "Tue", avgAmount: 1400, volume: 1810, suspicious: 14 },
    { label: "Wed", avgAmount: 1650, volume: 1930, suspicious: 15 },
    { label: "Thu", avgAmount: 1500, volume: 1870, suspicious: 13 },
    { label: "Fri", avgAmount: 2100, volume: 2240, suspicious: 21 },
    { label: "Sat", avgAmount: 2800, volume: 2480, suspicious: 31 },
    { label: "Sun", avgAmount: 1900, volume: 1990, suspicious: 18 },
  ],
  month: [
    { label: "Week 1", avgAmount: 1450, volume: 11800, suspicious: 74 },
    { label: "Week 2", avgAmount: 1620, volume: 12450, suspicious: 88 },
    { label: "Week 3", avgAmount: 1850, volume: 12980, suspicious: 96 },
    { label: "Week 4", avgAmount: 2400, volume: 13640, suspicious: 127 },
  ],
};

export const LOCATION_RISK: LocationRisk[] = [
  { city: "Hyderabad", lat: 17.385, lng: 78.4867, transactions: 1245, suspicious: 8 },
  { city: "Bangalore", lat: 12.9716, lng: 77.5946, transactions: 980, suspicious: 5 },
  { city: "Chennai", lat: 13.0827, lng: 80.2707, transactions: 1102, suspicious: 14 },
  { city: "Mumbai", lat: 19.076, lng: 72.8777, transactions: 1418, suspicious: 11 },
  { city: "Delhi", lat: 28.6139, lng: 77.209, transactions: 1330, suspicious: 9 },
  { city: "Pune", lat: 18.5204, lng: 73.8567, transactions: 742, suspicious: 3 },
  { city: "Kolkata", lat: 22.5726, lng: 88.3639, transactions: 611, suspicious: 6 },
];

export const USER_TIMELINE = [
  { time: "09:42", amount: 800, location: "Hyderabad", device: "Known Device", flagged: false },
  { time: "10:02", amount: 1200, location: "Hyderabad", device: "Known Device", flagged: false },
  { time: "10:35", amount: 2400, location: "Hyderabad", device: "Known Device", flagged: false },
  { time: "10:42", amount: 42000, location: "Chennai", device: "New Device", flagged: true },
];

export const DETECTION_FLOW = [
  "Transaction Received",
  "Feature Extraction",
  "ML Prediction",
  "Anomaly Detection",
  "Rule Engine",
  "Risk Aggregation",
  "Decision",
];
