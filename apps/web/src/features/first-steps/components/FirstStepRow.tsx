"use client";

import { Checkbox } from "@heroui/checkbox";
import type { KeyboardEvent } from "react";
import { FIRST_STEP_DEFINITIONS } from "@/features/first-steps/constants";
import type { FirstStepStatus } from "@/types/features/firstStepsTypes";

interface FirstStepRowProps {
  step: FirstStepStatus;
  onActivate: (step: FirstStepStatus) => void;
  /** Hide the one-line description (the banner has no room for it). */
  compact?: boolean;
}

/**
 * The checkbox mirrors server state and is read-only; clicking the row runs
 * the step's action instead of toggling anything.
 */
export function FirstStepRow({
  step,
  onActivate,
  compact = false,
}: FirstStepRowProps) {
  const { label, description, icon: Icon } = FIRST_STEP_DEFINITIONS[step.key];

  const activate = () => onActivate(step);
  // Without preventDefault the label click still toggles the native input, so
  // a done step would visibly un-tick until the next refetch. HeroUI intersects
  // React's and react-aria's handler types, so the event is typed by what we use.
  const handleClick = (event: { preventDefault: () => void }) => {
    event.preventDefault();
    activate();
  };
  const handleKeyDown = (event: KeyboardEvent<HTMLInputElement>) => {
    if (event.key === "Enter") activate();
  };

  return (
    <Checkbox
      isSelected={step.done}
      isReadOnly
      color="success"
      radius="full"
      size="sm"
      onClick={handleClick}
      onKeyDown={handleKeyDown}
      aria-label={label}
      classNames={{
        base: "m-0 max-w-none cursor-pointer rounded-xl px-2 py-1.5 transition-colors hover:bg-white/5",
        label: "flex items-center gap-2",
      }}
    >
      <Icon className="size-4 shrink-0 text-zinc-400" />
      <span className="flex min-w-0 flex-col">
        <span className="text-sm font-medium text-zinc-200">{label}</span>
        {!compact && (
          <span className="text-xs text-zinc-500">{description}</span>
        )}
      </span>
    </Checkbox>
  );
}
