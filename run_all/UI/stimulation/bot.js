#!/usr/bin/env node
/**
 * ===========================================================================
 * REAL-TIME PAYMENTS FRAUD DETECTION DASHBOARD
 * NODE.JS TRANSACTION SIMULATION BOT (100 TPS ENGINE)
 * ===========================================================================
 */

import fs from 'fs';
import path from 'path';
import http from 'http';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Color formatting
const Colors = {
  reset: "\x1b[0m",
  bright: "\x1b[1m",
  green: "\x1b[32m",
  yellow: "\x1b[33m",
  cyan: "\x1b[36m",
  red: "\x1b[31m",
  magenta: "\x1b[35m"
};

// Configuration
const DEFAULT_TPS = 100;
let targetTPS = DEFAULT_TPS;
let running = true;
let totalSent = 0;
let totalAnomalies = 0;
let totalBlocked = 0;
const anomalyCounts = {};

const ANOMALY_TYPES = [
  { name: "COMBINED_ANOMALY", weight: 0.0019, severity: "CRITICAL", baseRisk: 98.8 },
  { name: "HIGH_VELOCITY", weight: 0.0155, severity: "HIGH", baseRisk: 88.7 },
  { name: "NEW_DEVICE", weight: 0.0021, severity: "HIGH", baseRisk: 91.8 },
  { name: "UNUSUAL_AMOUNT", weight: 0.0020, severity: "HIGH", baseRisk: 80.6 },
  { name: "REPEATED_TRANSACTION", weight: 0.0045, severity: "MEDIUM", baseRisk: 63.1 },
  { name: "BEHAVIORAL_DRIFT", weight: 0.0020, severity: "MEDIUM", baseRisk: 46.1 },
  { name: "UNUSUAL_LOCATION", weight: 0.0019, severity: "HIGH", baseRisk: 82.7 },
  { name: "MULTIPLE_NEW_MERCHANTS", weight: 0.0018, severity: "MEDIUM", baseRisk: 37.8 },
  { name: "NEW_RECEIVER", weight: 0.0023, severity: "LOW", baseRisk: 45.5 },
  { name: "UNUSUAL_TIME", weight: 0.0020, severity: "LOW", baseRisk: 37.2 },
  { name: "NONE", weight: 0.9640, severity: "NONE", baseRisk: 18.0 }
];

const CITIES = ["Hyderabad", "Bangalore", "Chennai", "Mumbai", "Delhi", "Pune", "Kolkata"];
const MERCHANTS = ["Swiggy", "Zomato", "Amazon", "Flipkart", "BigBasket", "Croma Electronics", "IRCTC", "Apollo Pharmacy"];

// Parse CLI Args
const args = process.argv.slice(2);
for (let i = 0; i < args.length; i++) {
  if (args[i] === '--tps' && args[i+1]) {
    targetTPS = parseInt(args[i+1], 10) || DEFAULT_TPS;
  }
}

function sampleAnomaly() {
  const r = Math.random();
  let cumulative = 0;
  for (const item of ANOMALY_TYPES) {
    cumulative += item.weight;
    if (r <= cumulative) return item;
  }
  return ANOMALY_TYPES[ANOMALY_TYPES.length - 1]; // NONE
}

let txSeq = 1;
function generateTransaction() {
  const anomaly = sampleAnomaly();
  const isAnomaly = anomaly.name !== "NONE";
  const riskScore = isAnomaly 
    ? Math.min(99.0, Math.max(10.0, anomaly.baseRisk + (Math.random() * 10 - 5)))
    : Math.min(42.0, Math.max(4.0, 18.0 + (Math.random() * 20 - 10)));
  
  let status = "SAFE";
  if (riskScore >= 85) status = "BLOCKED";
  else if (riskScore >= 70) status = "SUSPICIOUS";
  else if (riskScore >= 45) status = "REVIEW";

  const now = new Date();
  const timeStr = now.toTimeString().split(' ')[0];
  const txId = `TXN_${String(txSeq++).padStart(9, '0')}`;

  const txn = {
    id: txId,
    timestamp: Date.now(),
    time: timeStr,
    userId: `USR_${Math.floor(10000 + Math.random() * 90000)}`,
    merchant: MERCHANTS[Math.floor(Math.random() * MERCHANTS.length)],
    amount: isAnomaly && anomaly.name === "UNUSUAL_AMOUNT" 
      ? Math.floor(25000 + Math.random() * 45000) 
      : Math.floor(200 + Math.random() * 4800),
    location: CITIES[Math.floor(Math.random() * CITIES.length)],
    device: anomaly.name === "NEW_DEVICE" || anomaly.name === "COMBINED_ANOMALY" ? "New Device" : "Known Device",
    deviceKnown: anomaly.name !== "NEW_DEVICE" && anomaly.name !== "COMBINED_ANOMALY",
    ip: `49.${Math.floor(Math.random()*200)}.${Math.floor(Math.random()*250)}.${Math.floor(Math.random()*250)}`,
    paymentMethod: "UPI",
    riskScore: Math.round(riskScore * 10) / 10,
    status,
    reason: isAnomaly ? `${anomaly.name}: Detected risk pattern` : undefined,

    // Raw ML dataset fields compatibility
    raw_dataset: {
      transaction_id: txId,
      user_id: `USR_${Math.floor(10000 + Math.random() * 90000)}`,
      timestamp: now.toISOString().replace('T', ' ').substring(0, 19),
      amount: Math.floor(200 + Math.random() * 4800),
      currency: "INR",
      payment_method: "UPI",
      is_anomaly: isAnomaly ? 1 : 0,
      anomaly_type: anomaly.name,
      anomaly_severity: anomaly.severity,
      risk_score: Math.round(riskScore * 10) / 10,
      status
    }
  };

  return txn;
}

// Simple embedded WebSocket / SSE Server for Frontend connection
const server = http.createServer((req, res) => {
  res.writeHead(200, {
    'Content-Type': 'application/json',
    'Access-Control-Allow-Origin': '*'
  });
  res.end(JSON.stringify({ status: "running", tps: targetTPS, totalSent }));
});

const serverPort = 8081;
server.listen(serverPort, () => {
  console.log(`${Colors.green}[Node.js Server] Control API running on http://localhost:${serverPort}${Colors.reset}`);
});

// Run Simulation Loop
console.log(`\n${Colors.bright}${Colors.magenta}=========================================================================${Colors.reset}`);
console.log(`${Colors.bright}${Colors.green} STARTING NODE.JS TRANSACTION SIMULATION BOT — TARGET: ${targetTPS} TPS${Colors.reset}`);
console.log(`${Colors.bright}${Colors.magenta}=========================================================================${Colors.reset}\n`);

const startTime = Date.now();
let lastCheck = Date.now();
let countLastInterval = 0;
let actualTPS = 0;

const intervalMs = 1000 / targetTPS;

const loop = setInterval(() => {
  if (!running) {
    clearInterval(loop);
    return;
  }

  const txn = generateTransaction();
  totalSent++;
  countLastInterval++;

  const atype = txn.raw_dataset.anomaly_type;
  if (atype !== "NONE") {
    totalAnomalies++;
    anomalyCounts[atype] = (anomalyCounts[atype] || 0) + 1;
  }

  if (txn.status === "BLOCKED") {
    totalBlocked++;
  }

  // Dashboard print every 500ms
  const now = Date.now();
  if (now - lastCheck >= 500) {
    actualTPS = (countLastInterval / (now - lastCheck)) * 1000;
    lastCheck = now;
    countLastInterval = 0;

    const elapsedSec = Math.floor((now - startTime) / 1000);
    process.stdout.write(
      `\r${Colors.bright}[SIMULATOR]${Colors.reset} ` +
      `Sent: ${Colors.green}${totalSent.toLocaleString()}${Colors.reset} | ` +
      `Target: ${Colors.cyan}${targetTPS} TPS${Colors.reset} | ` +
      `Actual: ${Colors.bright}${Colors.green}${actualTPS.toFixed(1)} TPS${Colors.reset} | ` +
      `Anomalies: ${Colors.yellow}${totalAnomalies.toLocaleString()}${Colors.reset} | ` +
      `Blocked: ${Colors.red}${totalBlocked.toLocaleString()}${Colors.reset} | ` +
      `Elapsed: ${elapsedSec}s `
    );
  }
}, Math.max(1, Math.floor(intervalMs)));

process.on('SIGINT', () => {
  running = false;
  clearInterval(loop);
  server.close();
  console.log(`\n\n${Colors.bright}${Colors.green}Node.js Simulation Complete! Total Sent: ${totalSent.toLocaleString()}${Colors.reset}\n`);
  process.exit(0);
});
