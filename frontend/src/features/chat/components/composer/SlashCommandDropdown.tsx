import { Button } from "@heroui/button";
import { Input } from "@heroui/input";
import { ScrollShadow } from "@heroui/scroll-shadow";
import { AnimatePresence, motion } from "framer-motion";
import { Hash, Search, X } from "lucide-react";
import React, { useMemo, useState } from "react";

import { SlashCommandMatch } from "@/features/chat/hooks/useSlashCommands";
import { formatToolName } from "@/features/chat/utils/chatUtils";
import { getToolCategoryIcon } from "@/features/chat/utils/toolIcons";
import { IntegrationsCard } from "@/features/integrations/components/IntegrationsCard";

import { CategoryIntegrationStatus } from "./CategoryIntegrationStatus";
import { LockedCategorySection } from "./LockedCategorySection";

interface SlashCommandDropdownProps {
  matches: SlashCommandMatch[];
  selectedIndex: number;
  onSelect: (tool: SlashCommandMatch) => void;
  onClose: () => void;
  position: { top?: number; bottom?: number; left: number; width?: number };
  isVisible: boolean;
  openedViaButton?: boolean;
}

const SlashCommandDropdown: React.FC<SlashCommandDropdownProps> = ({
  matches,
  selectedIndex,
  onSelect,
  onClose,
  position,
  isVisible,
  openedViaButton = false,
}) => {
  const [selectedCategory, setSelectedCategory] = useState<string>("all");
  const [searchQuery, setSearchQuery] = useState<string>("");

  // Get unique categories from matches
  const categories = useMemo(() => {
    const uniqueCategories = Array.from(
      new Set(matches.map((match) => match.tool.category)),
    );
    return ["all", ...uniqueCategories.sort()];
  }, [matches]);

  // Filter matches based on selected category and search query
  const filteredMatches = useMemo(() => {
    let filtered = matches;

    // Filter by category
    if (selectedCategory !== "all") {
      filtered = filtered.filter(
        (match) => match.tool.category === selectedCategory,
      );
    }

    // Filter by search query (when opened via button or slash command)
    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(
        (match) =>
          formatToolName(match.tool.name).toLowerCase().includes(query) ||
          match.tool.category.toLowerCase().includes(query),
      );
    }

    return filtered;
  }, [matches, selectedCategory, searchQuery, openedViaButton]);

  // Group tools by category and lock status
  const { unlockedMatches, lockedCategories } = useMemo(() => {
    const unlocked: SlashCommandMatch[] = [];
    const lockedByCategory: Record<string, SlashCommandMatch[]> = {};

    filteredMatches.forEach((match) => {
      const isLocked = match.enhancedTool?.isLocked || false;

      if (isLocked) {
        if (!lockedByCategory[match.tool.category]) {
          lockedByCategory[match.tool.category] = [];
        }
        lockedByCategory[match.tool.category].push(match);
      } else {
        unlocked.push(match);
      }
    });

    return {
      unlockedMatches: unlocked,
      lockedCategories: lockedByCategory,
    };
  }, [filteredMatches]);

  return (
    <AnimatePresence>
      {isVisible && matches.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: -8, scale: 0.95 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          exit={{ opacity: 0, y: -8, scale: 0.95 }}
          transition={{
            type: "spring",
            damping: 20,
            stiffness: 300,
            duration: 0.15,
          }}
          className="slash-command-dropdown fixed z-[200] overflow-hidden rounded-3xl border-1 border-zinc-700 bg-zinc-900/60 shadow-2xl backdrop-blur-2xl"
          style={{
            ...(position.top !== undefined && { top: 0, height: position.top }),
            ...(position.bottom !== undefined && {
              bottom: `calc(100vh - ${position.bottom - 2}px)`,
              maxHeight: position.bottom,
            }),
            left: position.left,
            width: position.width,
            transform: "none",
            boxShadow: "0px -18px 30px 5px rgba(0, 0, 0, 0.5)",
          }}
          onClick={(e) => e.stopPropagation()}
        >
          {/* Header section - Only show when opened via button */}
          {openedViaButton && (
            <div className="flex items-center gap-2 p-3">
              {/* Search Input */}
              <div className="flex-1">
                <Input
                  type="text"
                  placeholder="Search tools..."
                  value={searchQuery}
                  size="sm"
                  radius="full"
                  startContent={<Search size={16} />}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  autoFocus
                />
              </div>
              {/* Close Button */}
              <Button
                onPress={onClose}
                isIconOnly
                size="sm"
                radius="full"
                variant="flat"
              >
                <X size={14} />
              </Button>
            </div>
          )}

          {/* Category Tabs */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.1 }}
          >
            <ScrollShadow orientation="horizontal" className="overflow-x-auto">
              <div className="flex min-w-max gap-1 px-2 py-2">
                {/* <div className="grid min-w-max gap-1 px-2 py-2 grid-rows-2 grid-flow"> for 2 rows */}
                {categories.map((category) => (
                  <button
                    key={category}
                    onClick={(e) => {
                      e.stopPropagation();
                      setSelectedCategory(category);
                    }}
                    className={`flex cursor-pointer items-center gap-1.5 rounded-xl px-3 py-1.5 text-xs font-medium whitespace-nowrap transition-all ${
                      selectedCategory === category
                        ? "bg-zinc-700 text-white"
                        : "text-zinc-400 hover:bg-white/10 hover:text-zinc-300"
                    }`}
                  >
                    {category === "all" ? (
                      <Hash
                        size={16}
                        strokeWidth={2}
                        className="text-gray-400"
                      />
                    ) : (
                      getToolCategoryIcon(category)
                    )}
                    <span className="capitalize">
                      {category === "all" ? "All" : category.replace("_", " ")}
                    </span>
                    <CategoryIntegrationStatus category={category} />
                  </button>
                ))}
              </div>
            </ScrollShadow>
          </motion.div>

          {/* Tool List */}
          <div className="relative z-[1] h-fit max-h-96 overflow-y-auto">
            <div className="py-2">
              {/* Integrations Card - Only show in "all" category and when not filtering */}
              {selectedCategory === "all" &&
                (openedViaButton
                  ? !searchQuery.trim()
                  : matches.length === filteredMatches.length) && (
                  <IntegrationsCard onClose={onClose} />
                )}

              {/* Render unlocked tools first */}
              {unlockedMatches.map((match, index) => (
                <div
                  key={match.tool.name}
                  className={`relative mx-2 mb-1 cursor-pointer rounded-xl transition-all duration-150 ${
                    index === selectedIndex
                      ? "border border-zinc-600 bg-zinc-700/60"
                      : "border border-transparent hover:bg-white/5"
                  }`}
                  onClick={() => onSelect(match)}
                >
                  <div className="flex items-center gap-3 p-3">
                    {/* Icon */}
                    <div className="flex-shrink-0">
                      {getToolCategoryIcon(match.tool.category)}
                    </div>

                    {/* Content */}
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center justify-between gap-2">
                        <span className="truncate text-sm text-foreground-600">
                          {formatToolName(match.tool.name)}
                        </span>
                        {selectedCategory === "all" && (
                          <span className="rounded-full bg-zinc-600 px-2 py-0.5 text-xs text-zinc-200 capitalize">
                            {match.tool.category.replace("_", " ")}
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              ))}

              {/* Render locked categories as grouped sections */}
              {Object.entries(lockedCategories).map(
                ([category, categoryMatches]) => {
                  // Get integration info from the first tool in the category
                  const firstTool = categoryMatches[0];
                  const requiredIntegration =
                    firstTool.tool.required_integration;

                  if (!requiredIntegration) return null;

                  // Find integration name
                  const integrationName =
                    firstTool.enhancedTool?.integration?.integrationName ||
                    requiredIntegration;

                  return (
                    <LockedCategorySection
                      key={`locked-${category}`}
                      category={category}
                      tools={categoryMatches}
                      requiredIntegration={{
                        id: requiredIntegration,
                        name: integrationName,
                      }}
                      onConnect={onClose}
                    />
                  );
                },
              )}
            </div>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
};

export default SlashCommandDropdown;
