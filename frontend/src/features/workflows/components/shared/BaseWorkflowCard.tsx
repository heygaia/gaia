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
      .slice(0, 5)
      .map((category, index) => {
        const IconComponent = getToolCategoryIcon(category, {
          width: 25,
          height: 25,
        });
        return IconComponent ? (
          <div
            key={category}
            className="relative flex items-center justify-center"
            style={{ rotate: index % 2 == 0 ? "8deg" : "-8deg", zIndex: index }}
          >
            {IconComponent}
          </div>
        ) : null;
      })
      .filter(Boolean);

    if (validIcons.length === 0 && categories.length > 0) {
      validIcons.push(
        <ToolsIcon width={25} height={25} className="text-foreground-400" />,
      );
    }

    return (
      <>
        <div className="flex -space-x-1.5">{validIcons}</div>
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
      className={`group relative flex min-h-[195px] w-full flex-col gap-3 rounded-2xl bg-zinc-800 p-4 transition-all select-none ${
        onClick ? "cursor-pointer hover:bg-zinc-700/50" : ""
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
        <div className="mt-1 line-clamp-3 flex-1 text-xs text-zinc-400">
          {description}
        </div>
      </div>

      <div className="mt-auto">{footerContent}</div>
    </div>
  );
}
