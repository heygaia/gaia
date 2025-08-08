"use client";

import { Button } from "@heroui/button";
import { Chip } from "@heroui/chip";
import { Tab, Tabs } from "@heroui/tabs";
import { useEffect, useState } from "react";

import type { Plan } from "@/features/pricing/api/pricingApi";
import { pricingApi } from "@/features/pricing/api/pricingApi";
import { PricingCards } from "@/features/pricing/components/PricingCards";

export default function PricingPage() {
  const [plans, setPlans] = useState<Plan[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchPlans = async () => {
      try {
        setLoading(true);
        const plansData = await pricingApi.getPlans(true);
        setPlans(plansData);
        setError(null);
      } catch (err) {
        console.error("Failed to fetch plans:", err);
        setError(err instanceof Error ? err.message : "Failed to fetch plans");
      } finally {
        setLoading(false);
      }
    };

    fetchPlans();
  }, []);

  if (loading) {
    return (
      <div className="flex min-h-screen w-screen flex-col items-center justify-center py-28">
        <div className="flex flex-col items-center gap-4">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent"></div>
          <span className="text-foreground-500">Loading pricing plans...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex min-h-screen w-screen flex-col items-center justify-center py-28">
        <div className="flex flex-col items-center gap-4">
          <span className="text-danger">Error loading pricing plans</span>
          <span className="text-sm text-foreground-500">{error}</span>
          <Button onPress={() => window.location.reload()}>Retry</Button>
        </div>
      </div>
    );
  }
  return (
    <>
      <div className="flex min-h-screen w-screen flex-col items-center justify-center py-28">
        <div className="flex flex-col items-center gap-2">
          <div className="mb-2 flex w-full flex-col items-center gap-3">
            <Chip color="primary" size="lg" variant="light">
              Pricing
            </Chip>

            <span className="w-full px-6 text-center text-5xl font-medium">
              GAIA - Your Personal AI Assistant
            </span>
            <span className="text-md text-center text-foreground-500">
              Compare plans & features
            </span>
          </div>

          <div className="mt-5 flex w-full flex-col items-center font-medium">
            <Tabs aria-label="Options" radius="full">
              <Tab key="monthly" title="Monthly">
                <PricingCards durationIsMonth initialPlans={plans} />
              </Tab>
              <Tab
                key="yearly"
                title={
                  <div className="flex w-full items-center justify-center gap-2">
                    Yearly
                    <Chip color="primary" size="sm" variant="shadow">
                      <div className="text-sm font-medium">Save 25%</div>
                    </Chip>
                  </div>
                }
              >
                <PricingCards initialPlans={plans} />
              </Tab>
            </Tabs>
          </div>

          {/* <FAQAccordion /> */}
        </div>
      </div>
    </>
  );
}
