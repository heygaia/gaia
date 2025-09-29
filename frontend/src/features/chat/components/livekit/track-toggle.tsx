"use client";

import * as React from "react";

import { useTrackToggle } from "@livekit/components-react";
import { Track } from "livekit-client";
import { Loader2, Mic, MicOff } from "lucide-react";

import { Button } from "@/components/ui/shadcn/button";
import { cn } from "@/lib/utils";

export type TrackToggleProps = React.ComponentProps<typeof Button> & {
  source: Parameters<typeof useTrackToggle>[0]["source"];
  pending?: boolean;
  enabled?: boolean;
};

function getSourceIcon(
  source: Track.Source,
  enabled: boolean,
  pending = false,
) {
  if (pending) {
    return Loader2;
  }

  switch (source) {
    case Track.Source.Microphone:
      return enabled ? Mic : MicOff;
    default:
      return React.Fragment;
  }
}

export function TrackToggle({
  source,
  enabled,
  pending,
  className,
  onClick,
  ...props
}: TrackToggleProps) {
  const IconComponent = getSourceIcon(source, enabled ?? false, pending);

  return (
    <Button
      aria-label={`Toggle ${source}`}
      onClick={onClick}
      disabled={pending}
      className={cn(className)}
      {...props}
    >
      <IconComponent className={cn("!w-6 !h-6 text-white", pending && "animate-spin")} />
    </Button>
  );
}
