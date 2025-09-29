import {
  type TrackReference,
  useLocalParticipant,
  useVoiceAssistant,
} from "@livekit/components-react";
import { Track } from "livekit-client";
import { AnimatePresence, motion } from "motion/react";
import React, { useMemo } from "react";

import { cn } from "@/lib/utils";

import { AgentTile } from "./agent-tile";

const MotionAgentTile = motion.create(AgentTile);

const animationProps = {
  initial: {
    opacity: 0,
    scale: 0,
  },
  animate: {
    opacity: 1,
    scale: 1,
  },
  exit: {
    opacity: 0,
    scale: 0,
  },
  transition: {
    type: "spring" as const,
    stiffness: 675,
    damping: 75,
    mass: 1,
  },
};

const classNames = {
  grid: [
    "h-full w-full",
    "grid gap-x-2 place-content-center",
    "grid-cols-[1fr_1fr] grid-rows-[90px_1fr_90px]",
  ],
  // Agent
  // chatOpen: true,
  // hasSecondTile: false
  // layout: Column 1 / Row 1 / Column-Span 2
  // align: x-center y-center
  agentChatOpen: [
    "col-start-1 row-start-2",
    "col-span-2",
    "place-content-center",
  ],
  // Agent
  // chatOpen: false
  // layout: Column 1 / Row 1 / Column-Span 2 / Row-Span 3
  // align: x-center y-center
  agentChatClosed: [
    "col-start-1 row-start-1",
    "col-span-2 row-span-3",
    "place-content-center",
  ],
};

export function useLocalTrackRef(source: Track.Source) {
  const { localParticipant } = useLocalParticipant();
  const publication = localParticipant.getTrackPublication(source);
  const trackRef = useMemo<TrackReference | undefined>(
    () =>
      publication
        ? { source, participant: localParticipant, publication }
        : undefined,
    [source, publication, localParticipant],
  );
  return trackRef;
}

interface MediaTilesProps {
  chatOpen: boolean;
}

export function MediaTiles({ chatOpen }: MediaTilesProps) {
  const { state: agentState, audioTrack: agentAudioTrack } =
    useVoiceAssistant();

  const transition = {
    ...animationProps.transition,
    delay: chatOpen ? 0 : 0.15, // delay on close
  };
  const agentAnimate = {
    ...animationProps.animate,
    scale: chatOpen ? 1 : 3,
    transition: transition,
  };

  const agentLayoutTransition = transition;

  return (
      <div className="pointer-events-none mx-auto h-full max-w-2xl px-4 md:px-0">
        <div className={cn(classNames.grid)}>
          <div
            className={cn([
              'grid',
              // 'bg-[hotpink]', // for debugging
              !chatOpen && classNames.agentChatClosed,
              chatOpen && classNames.agentChatOpen,
            ])}
          >
            <AnimatePresence mode="popLayout">
                <MotionAgentTile
                  key="agent"
                  layoutId="agent"
                  {...animationProps}
                  animate={agentAnimate}
                  transition={agentLayoutTransition}
                  state={agentState}
                  audioTrack={agentAudioTrack}
                  className={cn(chatOpen ? 'h-[90px]' : 'h-auto w-full')}
                />
            </AnimatePresence>
          </div>
        </div>
      </div>
    );
}
