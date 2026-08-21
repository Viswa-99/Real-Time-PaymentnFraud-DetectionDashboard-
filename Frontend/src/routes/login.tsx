import { createFileRoute } from "@tanstack/react-router";
import { AuthCard } from "@/components/fraud/AuthCard";

export const Route = createFileRoute("/login")({
  head: () => ({
    meta: [
      { title: "Sign In | SentinelPay Fraud Platform" },
      {
        name: "description",
        content: "Secure analyst sign-in for the SentinelPay real-time payment fraud detection platform.",
      },
      { property: "og:title", content: "Sign In | SentinelPay Fraud Platform" },
      { property: "og:description", content: "Analyst access to real-time fraud monitoring." },
    ],
  }),
  component: () => <AuthCard mode="login" />,
});
