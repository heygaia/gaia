"use client";

import { Button } from "@heroui/button";
import { Chip } from "@heroui/chip";
import { Cancel01Icon } from "@icons";
import { twMerge } from "tailwind-merge";
import { FirstStepRow } from "@/features/first-steps/components/FirstStepRow";
import { useFirstStepAction } from "@/features/first-steps/hooks/useFirstStepAction";
import { useFirstSteps } from "@/features/first-steps/hooks/useFirstSteps";

interface FirstStepsBannerProps {
  className?: string;
}

/** Full-width activation checklist: one row on desktop, wraps on mobile. */
export function FirstStepsBanner({ className }: FirstStepsBannerProps) {
  const { steps, doneCount, totalCount, isVisible, dismiss, isDismissing } =
    useFirstSteps();
  const runStep = useFirstStepAction("banner");

  if (!isVisible) return null;

  return (
    <section
      aria-label="First steps"
      className={twMerge(
        "flex h-fit w-full flex-wrap items-center gap-x-2 gap-y-1 rounded-2xl bg-zinc-800 px-3 py-2",
        className,
      )}
    >
      <div className="flex items-center gap-2 pr-2">
        <p className="text-sm font-semibold text-zinc-100">First steps</p>
        <Chip size="sm" variant="flat">
          {doneCount}/{totalCount}
        </Chip>
      </div>
      <div className="flex min-w-0 flex-1 flex-wrap items-center gap-1">
        {steps.map((step) => (
          <FirstStepRow
            key={step.key}
            step={step}
            onActivate={runStep}
            compact
          />
        ))}
      </div>
      <Button
        isIconOnly
        size="sm"
        variant="light"
        aria-label="Dismiss first steps"
        isLoading={isDismissing}
        onPress={dismiss}
      >
        <Cancel01Icon className="size-4 text-zinc-400" />
      </Button>
    </section>
  );
}
