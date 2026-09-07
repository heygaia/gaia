import type { AgentCursorTarget } from "@/features/chat/components/bubbles/bot/AgentCursor";
import type {
  BrowserSessionStatus,
  BrowserStepSnapshot,
} from "@/types/features/browserTaskTypes";

/** Machine states → plain language the user understands at a glance. Shared by
 * the chat card and the browser side panel so the two never disagree. */
export const BROWSER_STATUS_META: Record<
  BrowserSessionStatus,
  {
    label: string;
    color: "default" | "primary" | "success" | "danger" | "warning";
  }
> = {
  starting: { label: "Starting", color: "default" },
  running: { label: "Working", color: "primary" },
  paused: { label: "Action needed", color: "warning" },
  completed: { label: "Done", color: "success" },
  failed: { label: "Couldn't finish", color: "danger" },
  cancelled: { label: "Stopped", color: "default" },
};

/** The origin the local `gaia-connect` tool must talk to: the web's API base
 * without its `/api/v1` path, since the tool appends that itself. */
export function connectApiOrigin(apiBaseUrl: string): string {
  return new URL(apiBaseUrl).origin;
}

export interface ConnectCommandOptions {
  apiOrigin: string;
  token: string;
  /** Passed as `--browser`; null lets the tool detect or ask. */
  browser: string | null;
}

/** The one command a user pastes to sync their browser's logins. */
export function buildConnectCommand({
  apiOrigin,
  token,
  browser,
}: ConnectCommandOptions): string {
  const parts = ["gaia-connect", "--api", apiOrigin, "--token", token];
  if (browser) parts.push("--browser", browser);
  return parts.join(" ");
}

/** "9:58" from seconds remaining, clamped at 0:00 once expired. */
export function formatCountdown(secondsLeft: number): string {
  const total = Math.max(0, Math.floor(secondsLeft));
  const minutes = Math.floor(total / 60);
  const seconds = String(total % 60).padStart(2, "0");
  return `${minutes}:${seconds}`;
}

/** Short relative time ("Just now", "5m ago", "Yesterday", "3d ago", then a date). */
export function formatRelativeDate(dateString: string): string {
  const date = new Date(dateString);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffSecs = Math.floor(diffMs / 1000);
  const diffMins = Math.floor(diffSecs / 60);
  const diffHours = Math.floor(diffMins / 60);
  const diffDays = Math.floor(diffHours / 24);

  if (diffSecs < 60) return "Just now";
  if (diffMins < 60) return `${diffMins}m ago`;
  if (diffHours < 24) return `${diffHours}h ago`;
  if (diffDays === 1) return "Yesterday";
  if (diffDays < 7) return `${diffDays}d ago`;

  return date.toLocaleDateString(undefined, { month: "short", day: "numeric" });
}

/** The agent's current cursor target — the latest step's last on-screen action.
 *
 * The point is a viewport fraction the runner resolves per action; the kind
 * drives the overlay (a click ripples, typing shows a caret). Returns null when
 * no recent action had an on-screen target (navigation, scroll, wait). */
export function latestAgentCursor(
  steps: BrowserStepSnapshot[],
): AgentCursorTarget | null {
  for (let i = steps.length - 1; i >= 0; i--) {
    const actions = steps[i].actions ?? [];
    for (let j = actions.length - 1; j >= 0; j--) {
      const action = actions[j];
      if (!action.point) continue;
      const [x, y] = action.point;
      const kind = /input|type|fill/i.test(action.name)
        ? "type"
        : /click|select|choose|tap/i.test(action.name)
          ? "click"
          : "move";
      const verb = kind === "type" ? "Typing" : "Clicking";
      const label = action.target
        ? `${verb} \u201c${action.target}\u201d`
        : verb;
      return { x, y, kind, label, key: steps[i].index * 100 + j };
    }
  }
  return null;
}
