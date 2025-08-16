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
  notion: "notion",
  linear: "productivity",
  web: "search",
  "web search": "search",
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
    <div className="group relative flex min-h-[280px] w-full cursor-pointer flex-col rounded-2xl border-1 border-zinc-800 bg-zinc-800 p-6 transition duration-300 hover:scale-105 hover:border-zinc-600">
      <ArrowUpRight
        className="absolute top-4 right-4 text-foreground-400 opacity-0 transition group-hover:opacity-100"
        width={25}
        height={25}
      />

      <div className="mb-4 flex items-center gap-3">
        {(() => {
          const validIcons = integrations
            .slice(0, 3)
            .map((integration) => {
              const category =
                integrationToCategory[integration] || integration;
              const IconComponent = getToolCategoryIcon(category, {
                width: 35,
                height: 35,
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
                width={35}
                height={35}
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

      <h3 className="mb- text-xl font-medium">{title}</h3>
      <div className="mb-4 line-clamp-3 flex-1 text-sm text-foreground-500">
        {description}
      </div>

      <div className="flex w-full flex-col gap-3">
        <Button
          color={action_type === "prompt" ? "primary" : "success"}
          variant="flat"
          size="md"
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
