"use client";

import { Button } from "@heroui/button";
import { Skeleton } from "@heroui/skeleton";
import { ArrowDown01Icon, ArrowUp01Icon, DragDropVerticalIcon } from "@icons";
import { Reorder, useDragControls } from "motion/react";
import Image from "next/image";
import type React from "react";
import { useChannelPriority } from "@/features/briefing/hooks/useChannelPriority";
import {
  NOTIFICATION_PLATFORM_ICONS,
  NOTIFICATION_PLATFORM_LABELS,
  NOTIFICATION_PLATFORMS,
  type NotificationPlatform,
} from "@/features/notification/constants";

interface ChannelPriorityListProps {
  /** Which platforms have a connected account (drives draggable vs. dimmed). */
  linkedMap: Record<NotificationPlatform, boolean>;
}

const dragSpring = { type: "spring", stiffness: 600, damping: 40 } as const;

function PlatformIcon({ platform }: { platform: NotificationPlatform }) {
  return (
    <Image
      src={NOTIFICATION_PLATFORM_ICONS[platform]}
      alt={NOTIFICATION_PLATFORM_LABELS[platform]}
      width={28}
      height={28}
      className="rounded-lg"
    />
  );
}

/**
 * A connected channel row. The grab handle initiates a drag; the up/down
 * buttons are the keyboard-reachable path to the same reorder-and-persist,
 * disabled at the ends of the list.
 */
function DraggableChannelRow({
  platform,
  isFirst,
  isLast,
  onDrop,
  onMove,
}: {
  platform: NotificationPlatform;
  isFirst: boolean;
  isLast: boolean;
  onDrop: () => void;
  onMove: (delta: -1 | 1) => void;
}) {
  const controls = useDragControls();
  const label = NOTIFICATION_PLATFORM_LABELS[platform];

  return (
    <Reorder.Item
      value={platform}
      dragListener={false}
      dragControls={controls}
      onDragEnd={onDrop}
      transition={dragSpring}
      whileDrag={{
        scale: 1.02,
        boxShadow: "0 12px 32px rgba(0,0,0,0.4)",
      }}
      className="flex select-none items-center gap-2 rounded-xl bg-zinc-800/60 px-2.5 py-2.5"
    >
      <Button
        isIconOnly
        size="sm"
        variant="light"
        radius="lg"
        aria-label={`Reorder ${label}`}
        onPointerDown={(event) => controls.start(event)}
        className="size-7 min-w-0 cursor-grab touch-none text-zinc-500 hover:text-zinc-300 active:cursor-grabbing"
      >
        <DragDropVerticalIcon className="size-4" />
      </Button>
      <PlatformIcon platform={platform} />
      <span className="flex-1 truncate text-sm text-zinc-200">{label}</span>
      <Button
        isIconOnly
        size="sm"
        variant="light"
        radius="lg"
        aria-label={`Move ${label} up`}
        isDisabled={isFirst}
        onPress={() => onMove(-1)}
        className="size-7 min-w-0 text-zinc-500 hover:text-zinc-300"
      >
        <ArrowUp01Icon className="size-4" />
      </Button>
      <Button
        isIconOnly
        size="sm"
        variant="light"
        radius="lg"
        aria-label={`Move ${label} down`}
        isDisabled={isLast}
        onPress={() => onMove(1)}
        className="size-7 min-w-0 text-zinc-500 hover:text-zinc-300"
      >
        <ArrowDown01Icon className="size-4" />
      </Button>
    </Reorder.Item>
  );
}

/** An unlinked channel: dimmed, non-draggable, nudged toward Linked Accounts. */
function UnlinkedChannelRow({ platform }: { platform: NotificationPlatform }) {
  const label = NOTIFICATION_PLATFORM_LABELS[platform];

  return (
    <div className="flex items-center gap-2 rounded-xl bg-zinc-800/30 px-2.5 py-2.5 opacity-50">
      <span className="flex size-7 items-center justify-center text-zinc-600">
        <DragDropVerticalIcon className="size-4" />
      </span>
      <PlatformIcon platform={platform} />
      <span className="flex-1 truncate text-sm text-zinc-400">{label}</span>
      <span className="shrink-0 text-xs text-zinc-500">
        Connect in Linked Accounts
      </span>
    </div>
  );
}

/**
 * Ordered list of briefing chat channels. Connected platforms are draggable
 * (drop persists optimistically); unlinked platforms pin to the bottom, dimmed.
 */
export const ChannelPriorityList: React.FC<ChannelPriorityListProps> = ({
  linkedMap,
}) => {
  const {
    isLoading,
    linkedOrder,
    unlinkedOrder,
    reorderLinked,
    persist,
    moveLinked,
  } = useChannelPriority(linkedMap);

  if (isLoading) {
    return (
      <div className="space-y-2">
        {NOTIFICATION_PLATFORMS.map((platform) => (
          <Skeleton key={platform} className="h-[46px] w-full rounded-xl" />
        ))}
      </div>
    );
  }

  return (
    <div className="space-y-2">
      <Reorder.Group
        axis="y"
        values={linkedOrder}
        onReorder={reorderLinked}
        className="space-y-2"
      >
        {linkedOrder.map((platform, index) => (
          <DraggableChannelRow
            key={platform}
            platform={platform}
            isFirst={index === 0}
            isLast={index === linkedOrder.length - 1}
            onDrop={persist}
            onMove={(delta) => moveLinked(platform, delta)}
          />
        ))}
      </Reorder.Group>
      {unlinkedOrder.length > 0 && (
        <div className="space-y-2">
          {unlinkedOrder.map((platform) => (
            <UnlinkedChannelRow key={platform} platform={platform} />
          ))}
        </div>
      )}
    </div>
  );
};
