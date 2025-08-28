"use client";

import { Button } from "@heroui/button";
import { ArrowUpRight, Play, Plus } from "lucide-react";

import { ToolsIcon } from "@/components";
import { getToolCategoryIcon } from "@/features/chat/utils/toolIcons";

// Map integration names to the categories used in getToolCategoryIcon
const integrationToCategory: Record<string, string> = {
  gmail: "mail",
  gcal: "calendar",
  calendar: "calendar",
  gdocs: "google_docs",
  "google-docs": "google_docs",
  google_docs: "google_docs",
  notion: "notion",
  linear: "productivity",
  web: "search",
  "web search": "search",
  search: "search",
  mail: "mail",
  email: "mail",
  productivity: "productivity",
  documents: "documents",
  development: "development",
  memory: "memory",
  creative: "creative",
  weather: "weather",
  goal_tracking: "goal_tracking",
  webpage: "webpage",
  support: "support",
  general: "general",
};

interface UseCaseCardProps {
  title: string;
  description: string;
  action_type: "prompt" | "workflow";
  integrations: string[];
}

export default function UseCaseCard({
  title,
  description,
  action_type,
  integrations,
}: UseCaseCardProps) {
  return (
    <div className="group relative flex min-h-[280px] w-full flex-col rounded-2xl border-1 border-zinc-800 bg-zinc-800 p-6 transition duration-300">
      <div className="mb-3 flex items-center gap-2">
        {(() => {
          const validIcons = integrations
            .slice(0, 3)
            .map((integration) => {
              const category =
                integrationToCategory[integration] || integration;
              const IconComponent = getToolCategoryIcon(category, {
                width: 25,
                height: 25,
              });
              return IconComponent ? (
                <div
                  key={integration}
                  className="flex items-center justify-center"
                >
                  {IconComponent}
                </div>
              ) : null;
            })
            .filter(Boolean);

          return validIcons.length > 0 ? (
            validIcons
          ) : (
            <div className="flex items-center justify-center">
              <ToolsIcon
                width={25}
                height={25}
                className="text-foreground-400"
              />
            </div>
          );
        })()}
        {integrations.length > 3 && (
          <div className="flex h-[40px] w-[40px] items-center justify-center rounded-lg bg-zinc-700 text-xs text-foreground-500">
            +{integrations.length - 3}
          </div>
        )}
      </div>

      <h3 className="text-xl font-medium">{title}</h3>
      <div className="mb-4 line-clamp-3 flex-1 text-sm text-foreground-500">
        {description}
      </div>

      <div className="flex w-full flex-col gap-3">
        <Button
          color="default"
          // color={action_type === "prompt" ? "primary" : "primary"}
          // variant="flat"
          size="sm"
          startContent={
            action_type === "prompt" ? (
              <Play width={16} height={16} />
            ) : (
              <Plus width={16} height={16} />
            )
          }
          className="w-full"
        >
          {action_type === "prompt" ? "Run Now" : "Create Workflow"}
        </Button>
      </div>
    </div>
  );
}
