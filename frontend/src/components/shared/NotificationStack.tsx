"use client";

import { Button } from "@heroui/button";
import { motion } from "framer-motion";
import { ArrowUpRight } from "lucide-react";
import { useState } from "react";

interface Notification {
  id: string;
  title: string;
  message: string;
  time: string;
  app: string;
}

const notifications: Notification[] = [
  {
    id: "1",
    title: "New Message",
    message: "Hey! How are you doing today? Want to grab coffee later?",
    time: "2m ago",
    app: "Messages",
  },
  {
    id: "2",
    title: "Email from Sarah",
    message:
      "Meeting rescheduled to 3 PM tomorrow. Please confirm your availability.",
    time: "5m ago",
    app: "Mail",
  },
  {
    id: "3",
    title: "Calendar Reminder",
    message: "Team standup meeting starts in 15 minutes",
    time: "10m ago",
    app: "Calendar",
  },
];

export default function NotificationStack() {
  const [isExpanded, setIsExpanded] = useState(false);

  const toggleExpanded = () => {
    setIsExpanded(!isExpanded);
  };

  return (
    <div className="mx-auto w-full max-w-3xs" onClick={toggleExpanded}>
      <motion.div
        initial={false}
        animate={{
          opacity: isExpanded ? 1 : 0,
          y: isExpanded ? 0 : -20,
          height: isExpanded ? "auto" : 0,
        }}
        transition={{
          duration: 0.3,
          type: "spring",
          stiffness: 150,
          damping: 19,
          mass: 1.2,
        }}
        className="overflow-hidden"
      >
        <div className="mb-3 flex items-center justify-between text-white">
          <h2 className="text-base font-medium select-none">Notifications</h2>
          <Button
            onPress={toggleExpanded}
            variant="flat"
            color="primary"
            className="text-primary"
            radius="full"
            size="sm"
          >
            {isExpanded ? "Collapse" : "Expand"}
          </Button>
        </div>
      </motion.div>

      <div
        className="relative"
        onClick={isExpanded ? undefined : toggleExpanded}
      >
        {notifications.map((notification, index) => {
          // Calculate stacked positions for collapsed state
          const stackOffset = index * 8; // Vertical offset when stacked
          const stackScale = 1 - index * 0.1; // Progressive scaling when stacked
          const stackOpacity = 1 - index * 0.4; // Slight opacity reduction for depth

          return (
            <motion.div
              key={notification.id}
              initial={false}
              animate={{
                y: isExpanded ? index * 62 : -stackOffset,
                scale: isExpanded ? 0.98 : index === 0 ? 1.02 : stackScale,
                opacity: isExpanded ? 1 : stackOpacity,
                zIndex: notifications.length - index,
              }}
              transition={{
                y: {
                  type: "spring",
                  stiffness: 320,
                  damping: 20,
                  mass: 0.4,
                },
                scale: {
                  type: "spring",
                  stiffness: 400,
                  damping: 25,
                  mass: 0.5,
                },
                opacity: {
                  duration: 0.2,
                },
                delay: isExpanded
                  ? index * 0.1
                  : (notifications.length - index - 1) * 0.1,
              }}
              className="group absolute top-0 right-0 left-0 flex min-h-10 w-full cursor-pointer items-center justify-center rounded-2xl bg-zinc-700 p-3 transition-colors select-none"
              style={{
                transformOrigin: "center top",
              }}
            >
              <div className="flex w-full items-start gap-1">
                {!isExpanded && index === 0 ? (
                  <div className="flex w-full items-center justify-center gap-2">
                    <div className="min-h-2 min-w-2 rounded-full bg-red-500" />
                    <p className="text-xs font-medium text-foreground-600">
                      You have {notifications.length} unread notification
                      {notifications.length === 1 ? "" : "s"}
                    </p>
                  </div>
                ) : (
                  isExpanded && (
                    <div className="w-full min-w-0 flex-1">
                      <div className="flex w-full items-center justify-between">
                        <h3 className="text-xs font-semibold text-foreground">
                          {notification.title}
                        </h3>
                        <span className="ml-2 flex-shrink-0 text-xs text-foreground-400">
                          {notification.time}
                        </span>
                      </div>
                      <p className="line-clamp-1 text-xs text-foreground-500">
                        {notification.message}
                      </p>
                    </div>
                  )
                )}
              </div>
            </motion.div>
          );
        })}
      </div>

      <motion.div
        initial={false}
        animate={{
          height: isExpanded ? notifications.length * 49 + 40 : 80,
          opacity: isExpanded ? 1 : 0,
        }}
        transition={{
          duration: 0.3,
          type: "spring",
          stiffness: 150,
          damping: 19,
          mass: 1.2,
        }}
        className="flex justify-center pt-4"
      />
      {isExpanded && (
        <div className="flex w-full justify-center">
          <Button
            href="/notifications"
            variant="light"
            className="flex gap-1 text-foreground-400"
            size="sm"
            endContent={<ArrowUpRight width={14} className="outline-0!" />}
          >
            View All
          </Button>
        </div>
      )}
    </div>
  );
}
