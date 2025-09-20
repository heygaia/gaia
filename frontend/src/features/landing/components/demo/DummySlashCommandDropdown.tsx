import { Button } from "@heroui/button";
import { Input } from "@heroui/input";
import { ScrollShadow } from "@heroui/scroll-shadow";
import { AnimatePresence, motion } from "framer-motion";
import { Check, Hash, Search, X } from "lucide-react";
import React, { useMemo, useState } from "react";

import { formatToolName } from "@/features/chat/utils/chatUtils";
import { getToolCategoryIcon } from "@/features/chat/utils/toolIcons";

// Dummy data based on the provided tools
const dummyTools = {
  tools: [
    {
      name: "fetch_gmail_messages",
      category: "mail",
      required_integration: "gmail",
    },
    {
      name: "search_gmail_messages",
      category: "mail",
      required_integration: "gmail",
    },
    {
      name: "compose_email",
      category: "mail",
      required_integration: "gmail",
    },
    {
      name: "get_email_thread",
      category: "mail",
      required_integration: "gmail",
    },
    {
      name: "get_mail_contacts",
      category: "mail",
      required_integration: "gmail",
    },
    {
      name: "create_todo",
      category: "productivity",
      required_integration: null,
    },
    {
      name: "list_todos",
      category: "productivity",
      required_integration: null,
    },
    {
      name: "update_todo",
      category: "productivity",
      required_integration: null,
    },
    {
      name: "delete_todo",
      category: "productivity",
      required_integration: null,
    },
    {
      name: "search_todos",
      category: "productivity",
      required_integration: null,
    },
    {
      name: "semantic_search_todos",
      category: "productivity",
      required_integration: null,
    },
    {
      name: "get_todo_statistics",
      category: "productivity",
      required_integration: null,
    },
    {
      name: "get_today_todos",
      category: "productivity",
      required_integration: null,
    },
    {
      name: "get_upcoming_todos",
      category: "productivity",
      required_integration: null,
    },
    {
      name: "create_project",
      category: "productivity",
      required_integration: null,
    },
    {
      name: "list_projects",
      category: "productivity",
      required_integration: null,
    },
    {
      name: "update_project",
      category: "productivity",
      required_integration: null,
    },
    {
      name: "delete_project",
      category: "productivity",
      required_integration: null,
    },
    {
      name: "get_todos_by_label",
      category: "productivity",
      required_integration: null,
    },
    {
      name: "get_all_labels",
      category: "productivity",
      required_integration: null,
    },
    {
      name: "bulk_complete_todos",
      category: "productivity",
      required_integration: null,
    },
    {
      name: "bulk_move_todos",
      category: "productivity",
      required_integration: null,
    },
    {
      name: "bulk_delete_todos",
      category: "productivity",
      required_integration: null,
    },
    {
      name: "add_subtask",
      category: "productivity",
      required_integration: null,
    },
    {
      name: "update_subtask",
      category: "productivity",
      required_integration: null,
    },
    {
      name: "delete_subtask",
      category: "productivity",
      required_integration: null,
    },
    {
      name: "create_reminder_tool",
      category: "productivity",
      required_integration: null,
    },
    {
      name: "list_user_reminders_tool",
      category: "productivity",
      required_integration: null,
    },
    {
      name: "get_reminder_tool",
      category: "productivity",
      required_integration: null,
    },
    {
      name: "delete_reminder_tool",
      category: "productivity",
      required_integration: null,
    },
    {
      name: "update_reminder_tool",
      category: "productivity",
      required_integration: null,
    },
    {
      name: "search_reminders_tool",
      category: "productivity",
      required_integration: null,
    },
    {
      name: "fetch_calendar_list",
      category: "calendar",
      required_integration: "google_calendar",
    },
    {
      name: "create_calendar_event",
      category: "calendar",
      required_integration: "google_calendar",
    },
    {
      name: "edit_calendar_event",
      category: "calendar",
      required_integration: "google_calendar",
    },
    {
      name: "fetch_calendar_events",
      category: "calendar",
      required_integration: "google_calendar",
    },
    {
      name: "search_calendar_events",
      category: "calendar",
      required_integration: "google_calendar",
    },
    {
      name: "view_calendar_event",
      category: "calendar",
      required_integration: "google_calendar",
    },
    {
      name: "create_goal",
      category: "goal_tracking",
      required_integration: null,
    },
    {
      name: "list_goals",
      category: "goal_tracking",
      required_integration: null,
    },
    {
      name: "get_goal",
      category: "goal_tracking",
      required_integration: null,
    },
    {
      name: "delete_goal",
      category: "goal_tracking",
      required_integration: null,
    },
    {
      name: "generate_roadmap",
      category: "goal_tracking",
      required_integration: null,
    },
    {
      name: "update_goal_node",
      category: "goal_tracking",
      required_integration: null,
    },
    {
      name: "search_goals",
      category: "goal_tracking",
      required_integration: null,
    },
    {
      name: "get_goal_statistics",
      category: "goal_tracking",
      required_integration: null,
    },
    {
      name: "create_google_doc_tool",
      category: "google_docs",
      required_integration: "google_docs",
    },
    {
      name: "list_google_docs_tool",
      category: "google_docs",
      required_integration: "google_docs",
    },
    {
      name: "get_google_doc_tool",
      category: "google_docs",
      required_integration: "google_docs",
    },
    {
      name: "update_google_doc_tool",
      category: "google_docs",
      required_integration: "google_docs",
    },
    {
      name: "format_google_doc_tool",
      category: "google_docs",
      required_integration: "google_docs",
    },
    {
      name: "share_google_doc_tool",
      category: "google_docs",
      required_integration: "google_docs",
    },
    {
      name: "search_google_docs_tool",
      category: "google_docs",
      required_integration: "google_docs",
    },
    {
      name: "generate_document",
      category: "documents",
      required_integration: null,
    },
    {
      name: "add_memory",
      category: "memory",
      required_integration: null,
    },
    {
      name: "search_memory",
      category: "memory",
      required_integration: null,
    },
    {
      name: "get_all_memory",
      category: "memory",
      required_integration: null,
    },
    {
      name: "execute_code",
      category: "development",
      required_integration: null,
    },
    {
      name: "create_flowchart",
      category: "development",
      required_integration: null,
    },
    {
      name: "generate_image",
      category: "creative",
      required_integration: null,
    },
    {
      name: "get_weather",
      category: "weather",
      required_integration: null,
    },
    {
      name: "create_support_ticket",
      category: "support",
      required_integration: null,
    },
    {
      name: "web_search_tool",
      category: "search",
      required_integration: null,
    },
    {
      name: "deep_research_tool",
      category: "search",
      required_integration: null,
    },
    {
      name: "fetch_webpages",
      category: "search",
      required_integration: null,
    },
    {
      name: "query_file",
      category: "documents",
      required_integration: null,
    },
  ],
  total_count: 66,
  categories: [
    "calendar",
    "creative",
    "development",
    "documents",
    "goal_tracking",
    "google_docs",
    "mail",
    "memory",
    "productivity",
    "search",
    "support",
    "weather",
  ],
};

interface DummySlashCommandDropdownProps {
  isVisible: boolean;
  onClose: () => void;
  openedViaButton?: boolean;
}

const DummySlashCommandDropdown: React.FC<DummySlashCommandDropdownProps> = ({
  isVisible,
  onClose,
  openedViaButton = false,
}) => {
  const [selectedCategory, setSelectedCategory] = useState<string>("all");
  const [searchQuery, setSearchQuery] = useState<string>("");

  const categories = useMemo(() => {
    return ["all", ...dummyTools.categories.sort()];
  }, []);

  const filteredTools = useMemo(() => {
    let filtered = dummyTools.tools;

    if (selectedCategory !== "all") {
      filtered = filtered.filter((tool) => tool.category === selectedCategory);
    }

    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(
        (tool) =>
          formatToolName(tool.name).toLowerCase().includes(query) ||
          tool.category.toLowerCase().includes(query),
      );
    }

    return filtered;
  }, [selectedCategory, searchQuery]);

  const handleToolClick = (toolName: string) => {
    // Do nothing - this is a dummy component
    console.log(`Clicked tool: ${toolName}`);
  };

  return (
    <AnimatePresence>
      {isVisible && (
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
          className="relative z-[200] mx-auto flex h-[50vh] w-full flex-col overflow-hidden rounded-3xl border-1 border-zinc-700 bg-zinc-900/60 shadow-2xl backdrop-blur-2xl"
          onClick={(e) => e.stopPropagation()}
        >
          {/* Header section - Only show when opened via button */}
          {openedViaButton && (
            <div className="flex items-center gap-2 p-3">
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
              <Button
                onPress={onClose}
                isIconOnly
                size="sm"
                radius="full"
                variant="flat"
                aria-label="Close button dummy composer"
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
                  </button>
                ))}
              </div>
            </ScrollShadow>
          </motion.div>

          {/* Tool List */}
          <div className="flex-1 overflow-y-auto">
            <div className="py-2">
              {filteredTools.map((tool) => (
                <div
                  key={tool.name}
                  className="relative mx-2 mb-1 cursor-pointer rounded-xl border border-transparent transition-all duration-150 hover:border-zinc-600 hover:bg-white/5"
                  onClick={() => handleToolClick(tool.name)}
                >
                  <div className="flex items-center gap-3 p-3">
                    <div className="flex-shrink-0">
                      {getToolCategoryIcon(tool.category)}
                    </div>

                    <div className="min-w-0 flex-1">
                      <div className="flex items-center justify-between gap-2">
                        <span className="truncate text-sm text-foreground-600">
                          {formatToolName(tool.name)}
                        </span>
                        <div className="flex items-center gap-2">
                          {selectedCategory === "all" && (
                            <span className="rounded-full bg-zinc-600 px-2 py-0.5 text-xs text-zinc-200 capitalize">
                              {tool.category.replace("_", " ")}
                            </span>
                          )}
                          {tool.required_integration && (
                            <div className="flex items-center gap-1">
                              <Check className="h-3 w-3 text-green-400" />
                              <span className="text-xs text-green-400">
                                Connected
                              </span>
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
};

export default DummySlashCommandDropdown;
