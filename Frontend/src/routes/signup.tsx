import { createFileRoute } from "@tanstack/react-router";
import { AuthCard } from "@/components/fraud/AuthCard";

export const Route = createFileRoute("/signup")({
  head: () => ({
    meta: [
      { title: "Create Account | SentinelPay Fraud Platform" },
      {
        name: "description",
        content: "Register an analyst account to monitor payments and investigate fraud in real time.",
      },
      { property: "og:title", content: "Create Account | SentinelPay Fraud Platform" },
      { property: "og:description", content: "Register for the SentinelPay fraud detection platform." },
    ],
  }),
  component: () => <AuthCard mode="signup" />,
});
