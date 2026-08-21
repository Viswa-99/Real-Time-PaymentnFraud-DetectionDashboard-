// Static model artifacts from Layer 2 error analysis + live transaction simulation.

export type Status = "APPROVED" | "UNDER_REVIEW" | "BLOCKED";

export const ANOMALY_TYPES = [
  "COMBINED_ANOMALY",
  "HIGH_VELOCITY",
  "NEW_DEVICE",
  "UNUSUAL_AMOUNT",
  "REPEATED_TRANSACTION",
  "BEHAVIORAL_DRIFT",
  "UNUSUAL_LOCATION",
  "MULTIPLE_NEW_MERCHANTS",
  "NEW_RECEIVER",
  "UNUSUAL_TIME",
] as const;

export type AnomalyType = (typeof ANOMALY_TYPES)[number] | "NONE";

export type Txn = {
  transaction_id: string;
  user_id: string;
  receiver_id?: string;
  merchant_id?: string;
  payment_method?: string;
  transaction_type?: string;
  amount: number;
  location: string;
  device: string;
  anomaly_type: AnomalyType;
  risk_probability: number;
  risk_score: number;
  layer1_anomaly_score: number;
  status: Status;
  timestamp: string;
  reasons?: { title: string; detail: string }[];
};

export const DETECTION_BY_TYPE = [
  { type: "COMBINED_ANOMALY", count: 312, detected: 312, rate: 100.0, meanRisk: 0.9881, medianRisk: 0.9893 },
  { type: "HIGH_VELOCITY", count: 2581, detected: 2215, rate: 85.82, meanRisk: 0.887, medianRisk: 0.9895 },
  { type: "NEW_DEVICE", count: 358, detected: 307, rate: 85.75, meanRisk: 0.9188, medianRisk: 0.9352 },
  { type: "UNUSUAL_AMOUNT", count: 340, detected: 193, rate: 56.76, meanRisk: 0.8066, medianRisk: 0.9253 },
  { type: "REPEATED_TRANSACTION", count: 750, detected: 375, rate: 50.0, meanRisk: 0.6318, medianRisk: 0.9111 },
  { type: "BEHAVIORAL_DRIFT", count: 339, detected: 25, rate: 7.37, meanRisk: 0.4616, medianRisk: 0.3952 },
  { type: "UNUSUAL_LOCATION", count: 322, detected: 22, rate: 6.83, meanRisk: 0.827, medianRisk: 0.8644 },
  { type: "MULTIPLE_NEW_MERCHANTS", count: 292, detected: 1, rate: 0.34, meanRisk: 0.378, medianRisk: 0.3487 },
  { type: "NEW_RECEIVER", count: 388, detected: 0, rate: 0.0, meanRisk: 0.4551, medianRisk: 0.4559 },
  { type: "UNUSUAL_TIME", count: 337, detected: 0, rate: 0.0, meanRisk: 0.3729, medianRisk: 0.3722 },
];

export const RISK_DISTRIBUTION = {
  count: 166937,
  mean: 0.301868,
  std: 0.157254,
  min: 0.045957,
  p1: 0.154918,
  p5: 0.165155,
  p10: 0.176555,
  p25: 0.203693,
  p50: 0.24447,
  p75: 0.35354,
  p90: 0.477106,
  p95: 0.565118,
  p99: 0.988999,
  max: 0.990504,
};

export const FALSE_POSITIVES = {
  count: 283,
  mean: 0.923554,
  std: 0.01788,
  min: 0.900002,
  p25: 0.906457,
  p50: 0.920172,
  p75: 0.939095,
  max: 0.98843,
};

export const FALSE_NEGATIVES = {
  count: 2569,
  mean: 0.438378,
  std: 0.214225,
  min: 0.087166,
  p25: 0.266805,
  p50: 0.381271,
  p75: 0.532083,
  max: 0.89928,
};

// Shared with the backend model contract: transactions at or above this score are blocked.
export const DECISION_THRESHOLD = 0.86;

export const TOP_LEGIT_HIGH_RISK = [
  ["TXN_000877669", "USR_047740", 0.98843, 98.843018, 0.547074],
  ["TXN_000938757", "USR_035089", 0.966707, 96.670723, 0.487239],
  ["TXN_000935397", "USR_025047", 0.965827, 96.582703, 0.601219],
  ["TXN_000991116", "USR_033211", 0.962072, 96.207199, 0.527426],
  ["TXN_000984703", "USR_002366", 0.962065, 96.206543, 0.529837],
  ["TXN_000853094", "USR_037418", 0.960742, 96.07415, 0.435494],
  ["TXN_000835343", "USR_007330", 0.959867, 95.986679, 0.624175],
  ["TXN_000852725", "USR_008205", 0.959866, 95.98661, 0.585917],
  ["TXN_000997196", "USR_035328", 0.959439, 95.943871, 0.429522],
  ["TXN_000952342", "USR_047706", 0.957488, 95.748772, 0.492711],
  ["TXN_000842333", "USR_035704", 0.957263, 95.726303, 0.453073],
  ["TXN_000911689", "USR_007440", 0.952895, 95.289459, 0.420761],
] as const;

export const TOP_MISSED = [
  ["TXN_000976760", "USR_001064", "UNUSUAL_LOCATION", 0.89928, 89.927986, 0.541485],
  ["TXN_000906090", "USR_016588", "NEW_DEVICE", 0.899056, 89.905617, 0.5106],
  ["TXN_000855215", "USR_018225", "UNUSUAL_LOCATION", 0.899031, 89.90313, 0.551977],
  ["TXN_000992509", "USR_006547", "UNUSUAL_AMOUNT", 0.898755, 89.875488, 0.475778],
  ["TXN_000895253", "USR_049616", "NEW_DEVICE", 0.8987, 89.870049, 0.546581],
  ["TXN_000836204", "USR_019568", "UNUSUAL_LOCATION", 0.898687, 89.868668, 0.481056],
  ["TXN_000920709", "USR_032313", "UNUSUAL_LOCATION", 0.898607, 89.860672, 0.486695],
  ["TXN_000961597", "USR_019712", "NEW_DEVICE", 0.898602, 89.860214, 0.591725],
  ["TXN_000893623", "USR_029673", "UNUSUAL_AMOUNT", 0.89829, 89.828987, 0.51002],
  ["TXN_000915529", "USR_045713", "UNUSUAL_LOCATION", 0.898236, 89.823578, 0.476528],
  ["TXN_000938365", "USR_035534", "MULTIPLE_NEW_MERCHANTS", 0.897682, 89.768227, 0.563757],
  ["TXN_000869694", "USR_011621", "BEHAVIORAL_DRIFT", 0.896551, 89.655151, 0.431674],
] as const;

const LOCATIONS = [
  "Mumbai, IN",
  "Bengaluru, IN",
  "Delhi, IN",
  "Singapore, SG",
  "London, UK",
  "New York, US",
  "Dubai, AE",
  "Frankfurt, DE",
];
const DEVICES = ["iOS-App", "Android-App", "Web-Chrome", "Web-Safari", "POS-Terminal"];

// Deterministic PRNG so SSR and client agree on the initial feed.
function mulberry32(seed: number) {
  return () => {
    seed |= 0;
    seed = (seed + 0x6d2b79f5) | 0;
    let t = Math.imul(seed ^ (seed >>> 15), 1 | seed);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

function pct(rand: () => number) {
  // Sample roughly matching the observed risk_probability distribution.
  const u = rand();
  if (u > 0.985) return 0.9 + rand() * 0.09;
  if (u > 0.93) return 0.7 + rand() * 0.2;
  if (u > 0.75) return 0.4 + rand() * 0.3;
  return 0.05 + rand() * 0.35;
}

export function makeTxn(rand: () => number, at: Date): Txn {
  const risk = pct(rand);
  const flagged = risk >= DECISION_THRESHOLD;
  const suspicious = risk >= 0.7;
  const anomaly: AnomalyType = suspicious
    ? ANOMALY_TYPES[Math.floor(rand() * ANOMALY_TYPES.length)]!
    : rand() > 0.92
      ? ANOMALY_TYPES[Math.floor(rand() * ANOMALY_TYPES.length)]!
      : "NONE";

  return {
    transaction_id: `TXN_${String(Math.floor(rand() * 999999)).padStart(6, "0")}`,
    user_id: `USR_${String(Math.floor(rand() * 49999)).padStart(6, "0")}`,
    amount: Math.round((10 + rand() * 4990) * 100) / 100,
    location: LOCATIONS[Math.floor(rand() * LOCATIONS.length)]!,
    device: DEVICES[Math.floor(rand() * DEVICES.length)]!,
    anomaly_type: anomaly,
    risk_probability: risk,
    risk_score: Math.round(risk * 1000000) / 10000,
    layer1_anomaly_score: Math.round((0.15 + rand() * 0.5) * 1e6) / 1e6,
    status: flagged ? "BLOCKED" : suspicious ? "UNDER_REVIEW" : "APPROVED",
    timestamp: at.toISOString(),
  };
}

export function seedFeed(n = 14, seed = 20260816): Txn[] {
  const rand = mulberry32(seed);
  const base = new Date("2026-08-16T15:00:00Z").getTime();
  return Array.from({ length: n }, (_, i) => makeTxn(rand, new Date(base - i * 9000)));
}

export function riskBand(p: number) {
  if (p >= 0.9) return { label: "90-100", tone: "critical" as const };
  if (p >= 0.7) return { label: "70-89", tone: "high" as const };
  if (p >= 0.4) return { label: "40-69", tone: "medium" as const };
  return { label: "0-39", tone: "low" as const };
}

export const ALERT_ACTIVITY = [
  { bucket: "-60m", critical: 2, high: 5, medium: 9 },
  { bucket: "-50m", critical: 1, high: 7, medium: 12 },
  { bucket: "-40m", critical: 4, high: 6, medium: 8 },
  { bucket: "-30m", critical: 3, high: 9, medium: 14 },
  { bucket: "-20m", critical: 6, high: 11, medium: 10 },
  { bucket: "-10m", critical: 2, high: 8, medium: 13 },
  { bucket: "now", critical: 5, high: 10, medium: 11 },
];

export const RISK_HISTOGRAM = [
  { band: "0.0-0.1", count: 1820 },
  { band: "0.1-0.2", count: 38940 },
  { band: "0.2-0.3", count: 71260 },
  { band: "0.3-0.4", count: 26410 },
  { band: "0.4-0.5", count: 13180 },
  { band: "0.5-0.6", count: 8240 },
  { band: "0.6-0.7", count: 3110 },
  { band: "0.7-0.8", count: 1290 },
  { band: "0.8-0.9", count: 810 },
  { band: "0.9-1.0", count: 1877 },
];
