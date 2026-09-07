import {
  BubbleChatIcon,
  PuzzleIcon,
  Rocket01Icon,
  SmartPhone01Icon,
  WorkflowSquare05Icon,
} from "@icons";
import type React from "react";
import type { FirstStepKey } from "@/types/features/firstStepsTypes";

export const FIRST_STEPS_QUERY_KEY = ["first-steps"] as const;

/** Routes where the floating widget must stay hidden: the onboarding wizard,
 * and the dashboard, which already shows the full-width banner. */
export const FIRST_STEPS_WIDGET_HIDDEN_PATHS: readonly string[] = [
  "/onboarding",
  "/dashboard",
];

export const SAY_HI_PROMPT = "What can you do for me?";

export type FirstStepAction =
  | { kind: "chat"; prompt: string }
  | { kind: "navigate"; href: string };

export interface FirstStepDefinition {
  label: string;
  description: string;
  icon: React.ComponentType<React.SVGProps<SVGSVGElement>>;
  action: FirstStepAction;
}

export const FIRST_STEP_DEFINITIONS: Record<FirstStepKey, FirstStepDefinition> =
  {
    say_hi: {
      label: "Say hi",
      description: "Ask GAIA what it can do for you",
      icon: BubbleChatIcon,
      action: { kind: "chat", prompt: SAY_HI_PROMPT },
    },
    connect_integration: {
      label: "Connect an integration",
      description: "Link Gmail, Calendar or another tool you use",
      icon: PuzzleIcon,
      action: { kind: "navigate", href: "/integrations" },
    },
    link_platform: {
      label: "Link a messaging app",
      description: "Chat with GAIA on WhatsApp, Telegram, Slack or Discord",
      icon: SmartPhone01Icon,
      action: { kind: "navigate", href: "/settings/linked-accounts" },
    },
    create_workflow: {
      label: "Create a workflow",
      description: "Automate something you do every week",
      icon: WorkflowSquare05Icon,
      action: { kind: "navigate", href: "/workflows" },
    },
    publish_workflow: {
      label: "Publish a workflow",
      description: "Share one of your workflows with the community",
      icon: Rocket01Icon,
      action: { kind: "navigate", href: "/workflows" },
    },
  };
