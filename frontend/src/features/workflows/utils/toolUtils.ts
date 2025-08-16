import { getToolCategoryIcon } from "@/features/chat/utils/toolIcons";
import { WorkflowStep } from "@/features/workflows/api/workflowApi";

// Tool name to category mapping based on backend registry
const TOOL_CATEGORY_MAP: Record<string, string> = {
  // Mail tools
  compose_email: "mail",
  search_gmail_messages: "mail",
  get_email_thread: "mail",
  list_gmail_messages: "mail",
  list_gmail_labels: "mail",
  apply_labels_to_emails: "mail",
  remove_labels_from_emails: "mail",
  archive_emails: "mail",
  star_emails: "mail",
  unstar_emails: "mail",
  create_gmail_label: "mail",
  delete_gmail_label: "mail",
  update_gmail_label: "mail",
  get_gmail_contacts: "mail",

  // Productivity tools
  create_todo_item: "productivity",
  list_todo_items: "productivity",
  get_todo_item: "productivity",
  update_todo_item: "productivity",
  delete_todo_item: "productivity",
  search_todo_items: "productivity",
  create_reminder_tool: "productivity",
  list_user_reminders_tool: "productivity",
  get_reminder_tool: "productivity",
  delete_reminder_tool: "productivity",
  update_reminder_tool: "productivity",
  search_reminders_tool: "productivity",
  create_workflow_tool: "productivity",
  get_workflow_tool: "productivity",
  list_workflows_tool: "productivity",
  execute_workflow_tool: "productivity",

  // Calendar tools
  list_calendar_events: "calendar",
  create_calendar_event: "calendar",
  update_calendar_event: "calendar",
  delete_calendar_event: "calendar",
  search_calendar_events: "calendar",

  // Goal tracking
  create_goal: "goal_tracking",
  list_goals: "goal_tracking",
  get_goal: "goal_tracking",
  update_goal: "goal_tracking",
  delete_goal: "goal_tracking",

  // Google Docs
  create_google_doc_tool: "google_docs",
  list_google_docs_tool: "google_docs",
  get_google_doc_tool: "google_docs",
  update_google_doc_tool: "google_docs",
  format_google_doc_tool: "google_docs",
  share_google_doc_tool: "google_docs",
  search_google_docs_tool: "google_docs",

  // Documents
  generate_document: "documents",
  query_file: "documents",

  // Search
  web_search_tool: "search",
  deep_research_tool: "search",
  fetch_webpages: "search",

  // Memory
  store_memory: "memory",
  retrieve_memory: "memory",
  search_memory: "memory",
  forget_memory: "memory",

  // Development
  execute_code: "development",
  create_flowchart: "development",

  // Creative
  generate_image: "creative",

  // Weather
  get_weather: "weather",

  // Support
  contact_support: "support",
  get_support_status: "support",
};

export const getToolCategory = (toolName: string): string => {
  return TOOL_CATEGORY_MAP[toolName] || "general";
};

export const getToolIcon = (toolName: string, iconProps = {}) => {
  const category = getToolCategory(toolName);
  return getToolCategoryIcon(category, iconProps);
};

export const getStepIcons = (steps: WorkflowStep[]) => {
  // Get unique categories from workflow steps
  const categories = [
    ...new Set(
      steps.map(
        (step) => step.tool_category || getToolCategory(step.tool_name),
      ),
    ),
  ];

  return categories.slice(0, 3); // Limit to 3 categories for display
};
