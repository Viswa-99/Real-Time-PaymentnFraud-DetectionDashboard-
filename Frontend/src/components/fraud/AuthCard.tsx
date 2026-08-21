import { Link, useNavigate } from "@tanstack/react-router";
import { useState } from "react";
import { Eye, EyeOff, ShieldCheck } from "lucide-react";
import { cn } from "@/lib/utils";

export function AuthCard({ mode }: { mode: "login" | "signup" }) {
  const navigate = useNavigate();
  const isSignup = mode === "signup";
  const [name, setName] = useState("");
  const [identifier, setIdentifier] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const validIdentifier = (v: string) =>
    /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v) || /^(\+91)?[6-9]\d{9}$/.test(v.replace(/\s/g, ""));

  function submit(e: React.FormEvent) {
    e.preventDefault();
    if (isSignup && name.trim().length < 2) return setError("Please enter your full name.");
    if (!validIdentifier(identifier))
      return setError("Enter a valid email address or 10-digit mobile number.");
    if (password.length < 8) return setError("Password must be at least 8 characters.");
    setError(null);
    // API-ready: POST /auth/login or POST /auth/signup
    void navigate({ to: "/" });
  }

  const field =
    "w-full rounded-lg border border-border bg-card px-3 py-2.5 text-sm text-foreground outline-none placeholder:text-muted-foreground focus:ring-2 focus:ring-ring/40";

  return (
    <div className="grid min-h-screen bg-background lg:grid-cols-2">
      <div className="hidden flex-col justify-between border-r border-border bg-card p-10 lg:flex">
        <div className="flex items-center gap-2.5">
          <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary text-primary-foreground">
            <ShieldCheck className="h-4 w-4" />
          </span>
          <div>
            <p className="text-sm font-semibold text-foreground">SentinelPay</p>
            <p className="text-[11px] text-muted-foreground">Fraud Intelligence Platform</p>
          </div>
        </div>
        <div className="max-w-md">
          <h2 className="text-2xl font-semibold tracking-tight text-foreground">
            Every payment monitored, scored and explained in real time.
          </h2>
          <p className="mt-3 text-sm text-muted-foreground">
            Behavioural baselines, geo-velocity checks, device fingerprinting and anomaly models
            combine into a single explainable risk score for every transaction.
          </p>
          <dl className="mt-8 grid grid-cols-3 gap-4">
            {[
              ["92.4%", "Detection rate"],
              ["84 ms", "Decision latency"],
              ["4.3%", "False positives"],
            ].map(([v, l]) => (
              <div key={l}>
                <dt className="num text-xl font-semibold text-foreground">{v}</dt>
                <dd className="text-xs text-muted-foreground">{l}</dd>
              </div>
            ))}
          </dl>
        </div>
        <p className="text-[11px] text-muted-foreground">
          Restricted system. Access is logged and monitored.
        </p>
      </div>

      <div className="flex items-center justify-center p-6">
        <form onSubmit={submit} className="w-full max-w-sm">
          <h1 className="text-xl font-semibold text-foreground">
            {isSignup ? "Create your analyst account" : "Sign in to SentinelPay"}
          </h1>
          <p className="mt-1 text-sm text-muted-foreground">
            {isSignup
              ? "Register with your work email or mobile number."
              : "Use your registered email or mobile number."}
          </p>

          <div className="mt-6 space-y-3">
            {isSignup ? (
              <div>
                <label className="mb-1.5 block text-xs font-medium text-foreground">Full name</label>
                <input
                  className={field}
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="Ananya Nair"
                />
              </div>
            ) : null}
            <div>
              <label className="mb-1.5 block text-xs font-medium text-foreground">
                Email or mobile number
              </label>
              <input
                className={field}
                value={identifier}
                onChange={(e) => setIdentifier(e.target.value)}
                placeholder="analyst@bank.com or 9876543210"
              />
            </div>
            <div>
              <label className="mb-1.5 block text-xs font-medium text-foreground">Password</label>
              <div className="relative">
                <input
                  className={cn(field, "pr-10")}
                  type={showPassword ? "text" : "password"}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="At least 8 characters"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword((s) => !s)}
                  aria-label="Toggle password visibility"
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground"
                >
                  {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </button>
              </div>
            </div>
          </div>

          {error ? (
            <p className="mt-3 rounded-lg border border-critical/30 bg-critical-soft px-3 py-2 text-xs text-critical">
              {error}
            </p>
          ) : null}

          <button
            type="submit"
            className="mt-5 w-full rounded-lg bg-primary py-2.5 text-sm font-semibold text-primary-foreground transition-opacity hover:opacity-90"
          >
            {isSignup ? "Create account" : "Sign in"}
          </button>

          <p className="mt-4 text-center text-xs text-muted-foreground">
            {isSignup ? "Already have an account? " : "New to SentinelPay? "}
            <Link
              to={isSignup ? "/login" : "/signup"}
              className="font-medium text-info hover:underline"
            >
              {isSignup ? "Sign in" : "Create an account"}
            </Link>
          </p>
        </form>
      </div>
    </div>
  );
}
