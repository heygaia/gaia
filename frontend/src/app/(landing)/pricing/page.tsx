import type { Metadata } from "next";

import PricingPage from "@/features/pricing/components/PricingPage";

export const metadata: Metadata = {
  title: "Pricing",
  description:
    "Compare GAIA's pricing plans and find the best AI assistant plan for your needs. Choose between monthly and yearly subscriptions.",
  openGraph: {
    title: "Pricing",
    description:
      "Compare GAIA's pricing plans and find the best AI assistant plan for your needs. Choose between monthly and yearly subscriptions.",
    url: "https://heygaia.io/pricing",
    images: ["/images/screenshot.webp"],
    siteName: "GAIA - AI Personal Assistant",
    type: "website",
  },
  twitter: {
    card: "summary_large_image",
    title: "Pricing",
    description:
      "Compare GAIA's pricing plans and find the best AI assistant plan for your needs. Choose between monthly and yearly subscriptions.",
    images: ["/images/screenshot.webp"],
  },
  keywords: [
    "GAIA",
    "Pricing",
    "AI Assistant",
    "Subscription Plans",
    "Monthly Plan",
    "Yearly Plan",
    "Compare Plans",
  ],
};

export default function Pricing() {
  return <PricingPage />;
}
