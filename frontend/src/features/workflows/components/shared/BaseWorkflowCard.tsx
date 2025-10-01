"use client";

import { Tooltip } from "@heroui/react";
import { ArrowUpRight, User } from "lucide-react";
import Image from "next/image";
import { ReactNode } from "react";

import { ToolsIcon } from "@/components";
import { getToolCategoryIcon } from "@/features/chat/utils/toolIcons";

interface BaseWorkflowCardProps {
  title: string;
  description: string;
  steps?: Array<{ tool_category: string }>;
  integrations?: string[];
  onClick?: () => void;
  showArrowIcon?: boolean;
  headerRight?: ReactNode;
  footerContent?: ReactNode;
  creator?: {
    name: string;
    avatar?: string;
  };
}

export default function BaseWorkflowCard({
  title,
  description,
  steps = [],
  integrations = [],
  onClick,
  showArrowIcon = false,
  headerRight,
  footerContent,
  creator,
}: BaseWorkflowCardProps) {
  const renderToolIcons = () => {
    let categories: string[];

    if (steps.length > 0)
      categories = [...new Set(steps.map((step) => step.tool_category))];
    else {
      // Handle integrations like in UseCaseCard
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
      categories = integrations.map(
        (integration) => integrationToCategory[integration] || integration,
      );
    }

    const validIcons = categories
      .slice(0, 3)
      .map((category) => {
        const IconComponent = getToolCategoryIcon(category, {
          width: 23,
          height: 23,
        });
        return IconComponent ? (
          <div key={category} className="flex items-center justify-center">
            {IconComponent}
          </div>
        ) : null;
      })
      .filter(Boolean);

    if (validIcons.length === 0 && categories.length > 0) {
      validIcons.push(
        <div key="default-tools" className="flex items-center justify-center">
          <ToolsIcon width={25} height={25} className="text-foreground-400" />
        </div>,
      );
    }

    return (
      <>
        {validIcons}
        {categories.length > 3 && (
          <div className="flex h-[25px] w-[25px] items-center justify-center rounded-lg bg-zinc-700 text-xs text-foreground-500">
            +{categories.length - 3}
          </div>
        )}
      </>
    );
  };

  return (
    <div
      className={`group relative flex min-h-[200px] w-full flex-col gap-3 rounded-2xl border-1 border-zinc-800 bg-zinc-800 p-4 transition-all select-none ${
        onClick ? "cursor-pointer hover:scale-105 hover:border-zinc-600" : ""
      }`}
      onClick={onClick}
    >
      {showArrowIcon && onClick && (
        <ArrowUpRight
          className="absolute top-4 right-4 text-foreground-400 opacity-0 transition group-hover:opacity-100"
          width={25}
          height={25}
        />
      )}
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-2">{renderToolIcons()}</div>
        {headerRight}
      </div>

      <div>
        <h3 className="line-clamp-1 text-lg font-medium">{title}</h3>
        <div className="line-clamp-3 flex-1 text-sm text-foreground-500">
          {description}
        </div>
      </div>

      {creator && (
        <Tooltip
          content="Created by"
          showArrow
          placement="left"
          color="foreground"
        >
          <div className="flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-full">
              {creator.avatar ? (
                <Image
                  src={creator.avatar}
                  alt={creator.name}
                  width={27}
                  height={27}
                  className="rounded-full"
                />
              ) : (
                <User className="h-4 w-4 text-zinc-400" />
              )}
            </div>
            <div className="flex min-w-0 flex-1 flex-col">
              <p className="truncate text-xs font-medium text-zinc-400">
                {creator.name}
              </p>
            </div>
          </div>
        </Tooltip>
      )}
      {footerContent}
    </div>
  );
}
