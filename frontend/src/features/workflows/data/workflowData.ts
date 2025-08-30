export interface TriggerOption {
  id: string;
  name: string;
  icon: string;
  description: string;
}

export interface IntegrationOption {
  id: string;
  name: string;
  icon: string;
  category: string;
}

export const triggerOptions: TriggerOption[] = [
  {
    id: "slack",
    name: "Slack",
    icon: "https://cdn.jsdelivr.net/gh/devicons/devicon/icons/slack/slack-original.svg",
    description: "Trigger when new messages arrive",
  },
  {
    id: "gmail",
    name: "Gmail",
    icon: "https://upload.wikimedia.org/wikipedia/commons/7/7e/Gmail_icon_%282020%29.svg",
    description: "Trigger when new emails arrive",
  },
  {
    id: "calendar",
    name: "Google Calendar",
    icon: "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a5/Google_Calendar_icon_%282020%29.svg/640px-Google_Calendar_icon_%282020%29.svg.png",
    description: "Trigger when new events are created",
  },
];

export const integrationOptions: IntegrationOption[] = [
  {
    id: "notion",
    name: "Notion",
    icon: "https://upload.wikimedia.org/wikipedia/commons/4/45/Notion_app_logo.png",
    category: "productivity",
  },
  {
    id: "google-docs",
    name: "Google Docs",
    icon: "https://upload.wikimedia.org/wikipedia/commons/thumb/6/66/Google_Docs_2020_Logo.svg/640px-Google_Docs_2020_Logo.svg.png",
    category: "documents",
  },
  {
    id: "google-drive",
    name: "Google Drive",
    icon: "https://upload.wikimedia.org/wikipedia/commons/thumb/1/12/Google_Drive_icon_%282020%29.svg/640px-Google_Drive_icon_%282020%29.svg.png",
    category: "storage",
  },
  {
    id: "gmail",
    name: "Gmail",
    icon: "https://upload.wikimedia.org/wikipedia/commons/7/7e/Gmail_icon_%282020%29.svg",
    category: "communication",
  },
  {
    id: "google-calendar",
    name: "Google Calendar",
    icon: "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a5/Google_Calendar_icon_%282020%29.svg/640px-Google_Calendar_icon_%282020%29.svg.png",
    category: "productivity",
  },
  {
    id: "slack",
    name: "Slack",
    icon: "https://cdn.jsdelivr.net/gh/devicons/devicon/icons/slack/slack-original.svg",
    category: "communication",
  },
];

export const scheduleFrequencyOptions = [
  { key: "every", label: "Every" },
  { key: "once", label: "Once" },
];

export const intervalOptions = [
  { key: "day", label: "Day" },
  { key: "week", label: "Week" },
  { key: "month", label: "Month" },
];

export const dayOptions = [
  { key: "monday", label: "Monday" },
  { key: "tuesday", label: "Tuesday" },
  { key: "wednesday", label: "Wednesday" },
  { key: "thursday", label: "Thursday" },
  { key: "friday", label: "Friday" },
  { key: "saturday", label: "Saturday" },
  { key: "sunday", label: "Sunday" },
];

export const monthOptions = [
  { key: "1", label: "1st" },
  { key: "2", label: "2nd" },
  { key: "3", label: "3rd" },
  { key: "4", label: "4th" },
  { key: "5", label: "5th" },
  { key: "6", label: "6th" },
  { key: "7", label: "7th" },
  { key: "8", label: "8th" },
  { key: "9", label: "9th" },
  { key: "10", label: "10th" },
  { key: "11", label: "11th" },
  { key: "12", label: "12th" },
  { key: "13", label: "13th" },
  { key: "14", label: "14th" },
  { key: "15", label: "15th" },
  { key: "16", label: "16th" },
  { key: "17", label: "17th" },
  { key: "18", label: "18th" },
  { key: "19", label: "19th" },
  { key: "20", label: "20th" },
  { key: "21", label: "21st" },
  { key: "22", label: "22nd" },
  { key: "23", label: "23rd" },
  { key: "24", label: "24th" },
  { key: "25", label: "25th" },
  { key: "26", label: "26th" },
  { key: "27", label: "27th" },
  { key: "28", label: "28th" },
  { key: "29", label: "29th" },
  { key: "30", label: "30th" },
  { key: "31", label: "31st" },
];
