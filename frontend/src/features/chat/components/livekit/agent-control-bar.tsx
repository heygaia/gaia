"use client";

import * as React from "react";

import { useRemoteParticipants } from "@livekit/components-react";
import { Track } from "livekit-client";
import { MessageCircle, PhoneOff } from "lucide-react";

import { Button } from "@/components/ui/shadcn/button";
import {
  UseAgentControlBarProps,
  useAgentControlBar,
} from "@/features/chat/components/livekit/hooks/use-agent-control-bar";
import { TrackToggle } from "@/features/chat/components/livekit/track-toggle";
import { cn } from "@/lib/utils";

export interface AgentControlBarProps
  extends React.HTMLAttributes<HTMLDivElement>,
    UseAgentControlBarProps {
  onChatOpenChange?: (open: boolean) => void;
  onDisconnect?: () => void;
  _onDeviceError?: (error: { source: Track.Source; error: Error }) => void;
}

/**
 * A control bar specifically designed for voice assistant interfaces
 */
export function AgentControlBar({
  controls,
  saveUserChoices = true,
  className,
  onChatOpenChange,
  onDisconnect,
  _onDeviceError,
  ...props
}: AgentControlBarProps) {
  const participants = useRemoteParticipants();
  const [chatOpen, setChatOpen] = React.useState(false);
  const isAgentAvailable = participants.some((p) => p.isAgent);
  const [isDisconnecting, setIsDisconnecting] = React.useState(false);

  const { visibleControls, microphoneToggle, handleDisconnect } =
    useAgentControlBar({
      controls,
      saveUserChoices,
    });

  const onLeave = async () => {
    setIsDisconnecting(true);
    handleDisconnect();
    setIsDisconnecting(false);
    onDisconnect?.();
  };

  React.useEffect(() => {
    onChatOpenChange?.(chatOpen);
  }, [chatOpen, onChatOpenChange]);

  return (
    <div
      aria-label="Voice assistant controls"
      className={cn("flex flex-col items-center justify-center p-3", className)}
      {...props}
    >
      <div className="flex flex-row items-center justify-center gap-6">
        <div className="flex items-center justify-center">
          <TrackToggle
            source={Track.Source.Microphone}
            enabled={microphoneToggle.enabled}
            pending={microphoneToggle.pending}
            onClick={() => microphoneToggle.toggle()}
            className="flex h-16 w-16 items-center justify-center rounded-full bg-gray-700/20 shadow-md transition-colors hover:bg-gray-700/30 active:bg-gray-700/30"
          />
        </div>

        <div className="flex items-center justify-center">
          <Button
            aria-label="Toggle chat"
            onClick={() => setChatOpen((prev) => !prev)}
            disabled={!isAgentAvailable}
            className="flex h-16 w-16 items-center justify-center rounded-full bg-gray-700/20 shadow-md transition-colors hover:bg-gray-700/30 active:bg-gray-700/30"
          >
            <MessageCircle className="!h-6 !w-6 text-white" />
          </Button>
        </div>

        {visibleControls.leave && (
          <div className="flex items-center justify-center">
            <Button
              onClick={onLeave}
              disabled={isDisconnecting}
              className="flex h-16 w-16 items-center justify-center rounded-full bg-red-500/10 shadow-md transition-colors hover:bg-red-500/15 active:bg-red-500/20"
            >
              <PhoneOff className="!h-6 !w-6 text-red-400" />
            </Button>
          </div>
        )}
      </div>
    </div>
  );
}
