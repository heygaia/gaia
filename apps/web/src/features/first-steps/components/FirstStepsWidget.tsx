"use client";

import { Button } from "@heroui/button";
import { Chip } from "@heroui/chip";
import { ArrowDown01Icon, ArrowUp01Icon, Cancel01Icon } from "@icons";
import { useState } from "react";
import { FirstStepRow } from "@/features/first-steps/components/FirstStepRow";
import { FIRST_STEPS_WIDGET_HIDDEN_PATHS } from "@/features/first-steps/constants";
import { useFirstStepAction } from "@/features/first-steps/hooks/useFirstStepAction";
import { useFirstSteps } from "@/features/first-steps/hooks/useFirstSteps";
import { usePathname } from "@/i18n/navigation";

/** Floating bottom-right version of the checklist, mounted once in the main layout. */
export function FirstStepsWidget() {
  const pathname = usePathname();
  const { steps, doneCount, totalCount, isVisible, dismiss, isDismissing } =
    useFirstSteps();
  const runStep = useFirstStepAction("widget");
  const [collapsed, setCollapsed] = useState(false);

  if (FIRST_STEPS_WIDGET_HIDDEN_PATHS.includes(pathname) || !isVisible) {
    return null;
  }

  const CollapseIcon = collapsed ? ArrowUp01Icon : ArrowDown01Icon;

  return (
    <aside
      aria-label="First steps"
      className="fixed right-4 bottom-4 z-40 w-[calc(100vw-2rem)] max-w-80 rounded-2xl bg-zinc-800 p-3 shadow-lg"
    >
      <div className="flex items-center gap-2">
        <p className="text-sm font-semibold text-zinc-100">First steps</p>
        <Chip size="sm" variant="flat">
          {doneCount}/{totalCount}
        </Chip>
        <div className="ml-auto flex items-center">
          <Button
            isIconOnly
            size="sm"
            variant="light"
            aria-label={
              collapsed ? "Expand first steps" : "Collapse first steps"
            }
            onPress={() => setCollapsed((value) => !value)}
          >
            <CollapseIcon className="size-4 text-zinc-400" />
          </Button>
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
        </div>
      </div>
      {!collapsed && (
        <div className="mt-2 flex flex-col gap-1">
          {steps.map((step) => (
            <FirstStepRow key={step.key} step={step} onActivate={runStep} />
          ))}
        </div>
      )}
    </aside>
  );
}
