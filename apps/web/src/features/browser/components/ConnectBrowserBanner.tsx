"use client";

import { Button } from "@heroui/button";
import { ArcBrowserIcon, ChromeIcon, EdgeStyleIcon } from "@icons";

const BROWSER_LOGOS = [
  { label: "Arc", icon: ArcBrowserIcon },
  { label: "Chrome", icon: ChromeIcon },
  { label: "Edge", icon: EdgeStyleIcon },
] as const;

interface ConnectBrowserBannerProps {
  /** With logins present the banner shrinks to a quiet "sync more" strip. */
  hasLogins: boolean;
  onConnect: () => void;
}

/** Full-width entry point to syncing a local browser's logins. Loud when the
 * list is empty (the fastest way to a useful saved-sites list), quiet once it
 * isn't. */
export function ConnectBrowserBanner({
  hasLogins,
  onConnect,
}: ConnectBrowserBannerProps) {
  if (hasLogins) {
    return (
      <div className="flex items-center justify-between gap-3 rounded-2xl bg-zinc-800/40 px-4 py-3">
        <p className="text-sm text-zinc-400">
          Sync more sites from your browser.
        </p>
        <Button
          size="sm"
          variant="flat"
          className="h-8 shrink-0"
          onPress={onConnect}
        >
          Connect browser
        </Button>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-4 rounded-2xl bg-zinc-800 p-4 sm:flex-row sm:items-center sm:justify-between">
      <div className="flex items-center gap-4">
        <div className="flex shrink-0 -space-x-2">
          {BROWSER_LOGOS.map(({ label, icon: Icon }) => (
            <span
              key={label}
              className="flex size-9 items-center justify-center rounded-full bg-zinc-900 ring-2 ring-zinc-800"
            >
              <Icon className="size-4 text-zinc-200" />
            </span>
          ))}
        </div>
        <div className="min-w-0">
          <p className="font-medium text-sm text-zinc-100">
            Already signed in on your computer?
          </p>
          <p className="mt-0.5 text-xs text-zinc-400 leading-relaxed">
            Sync your browser's logins so GAIA can skip the sign-in on sites you
            already use.
          </p>
        </div>
      </div>
      <Button
        color="primary"
        size="sm"
        className="shrink-0"
        onPress={onConnect}
      >
        Connect my browser
      </Button>
    </div>
  );
}
