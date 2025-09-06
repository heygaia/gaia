"use client";

import { Button } from "@heroui/button";
import {
  Badge,
  Popover,
  PopoverContent,
  PopoverTrigger,
  Tab,
  Tabs,
  Tooltip,
} from "@heroui/react";
import { formatDistanceToNow } from "date-fns";
import { CheckCheck } from "lucide-react";
import { useRouter } from "next/navigation";
import { useMemo, useState } from "react";
import { toast } from "sonner";

import { SidebarHeaderButton } from "@/components/";
import { ConfirmationDialog } from "@/components/shared/ConfirmationDialog";
import { ScrollArea } from "@/components/ui/shadcn/scroll-area";
import { useNotifications } from "@/features/notification/hooks/useNotifications";
import { useConfirmation } from "@/hooks/useConfirmation";

import { NotificationIcon } from "../../../components/shared";
import {
  NotificationAction,
  NotificationRecord,
  NotificationStatus,
} from "../../../types/features/notificationTypes";

interface NotificationCenterProps {
  className?: string;
}

const NotificationItem = ({
  notification,
  onMarkAsRead,
}: {
  notification: NotificationRecord;
  onMarkAsRead: (id: string) => void;
}) => {
  const { confirm, confirmationProps } = useConfirmation();
  const [executingActionId, setExecutingActionId] = useState<string | null>(
    null,
  );

  // Access content directly from notification
  const content = notification.content || {
    title: "Notification",
    body: "No details available",
    actions: [],
  };

  const isUnread = notification.status === NotificationStatus.DELIVERED;

  return (
    <div className={`w-full rounded-2xl bg-zinc-900 p-4`}>
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2">
            <h4 className="max-w-[250px] truncate text-sm font-medium text-zinc-100">
              {content.title}
            </h4>
            {isUnread && (
              <div className="h-1.5 w-1.5 flex-shrink-0 rounded-full bg-primary" />
            )}
          </div>
          <p className="my-1 line-clamp-2 text-left text-sm font-light break-words text-zinc-400">
            {content.body}
          </p>
          <div className="mt-1 flex items-center gap-2 text-xs text-zinc-600">
            <span className="capitalize">
              {formatDistanceToNow(new Date(notification.created_at), {
                addSuffix: true,
              })}
            </span>
            <span className="rounded-full bg-zinc-800 px-2 py-0.5 text-xs text-zinc-400 capitalize">
              {notification.metadata?.reminder_id ? "reminder" : "system"}
            </span>
          </div>
        </div>

        {isUnread && (
          <div className="flex flex-shrink-0 items-center gap-1">
            <Tooltip content="Mark as Read">
              <Button
                variant="flat"
                size="sm"
                isIconOnly
                onPress={() => onMarkAsRead(notification.id)}
                title="Mark as read"
              >
                <CheckCheck className="h-3.5 w-3.5" />
              </Button>
            </Tooltip>
          </div>
        )}
      </div>

      {/* Actions buttons if present */}
      {content.actions &&
        Array.isArray(content.actions) &&
        content.actions.length > 0 && (
          <div className="mt-3 flex gap-2">
            {content.actions.map((action: NotificationAction) => {
              const isExecuted = action.executed || false;
              const isCurrentlyExecuting = executingActionId === action.id;
              const isDisabled =
                action.disabled || isExecuted || isCurrentlyExecuting;

              return (
                <Button
                  key={action.id}
                  variant={action.style === "primary" ? "solid" : "flat"}
                  size="sm"
                  className={`h-7 bg-zinc-800/50 text-xs text-zinc-200 hover:bg-zinc-800/70 ${
                    isExecuted ? "cursor-not-allowed opacity-50" : ""
                  }`}
                  disabled={isDisabled}
                  onPress={async () => {
                    if (isDisabled) return;

                    try {
                      if (
                        action.requires_confirmation &&
                        action.confirmation_message
                      ) {
                        const confirmed = await confirm({
                          title: "Confirm Action",
                          message: action.confirmation_message,
                          confirmText: "Continue",
                          cancelText: "Cancel",
                          variant:
                            action.style === "danger"
                              ? "destructive"
                              : "default",
                        });
                        if (!confirmed) return;
                      }

                      setExecutingActionId(action.id);

                      const { NotificationsAPI } = await import(
                        "@/services/api/notifications"
                      );
                      const result = await NotificationsAPI.executeAction(
                        notification.id,
                        action.id,
                      );

                      if (result.success) {
                        toast.success(
                          result.message || "Action executed successfully",
                        );
                        // Optionally trigger a refresh here if needed
                      } else {
                        toast.error(
                          result.message || "Failed to execute action",
                        );
                      }
                    } catch (error) {
                      console.error("Action execution failed:", error);
                      toast.error("Failed to execute action");
                    } finally {
                      setExecutingActionId(null);
                    }
                  }}
                >
                  {isCurrentlyExecuting ? (
                    <div className="flex items-center gap-1">
                      <div className="h-3 w-3 animate-spin rounded-full border border-current border-t-transparent" />
                      <span>Processing...</span>
                    </div>
                  ) : (
                    <>
                      {action.label}
                      {isExecuted && <span className="ml-1">✓</span>}
                    </>
                  )}
                </Button>
              );
            })}
          </div>
        )}

      {/* Confirmation Dialog */}
      <ConfirmationDialog {...confirmationProps} />
    </div>
  );
};

export function NotificationCenter({
  className = "",
}: NotificationCenterProps) {
  const [activeTab, setActiveTab] = useState<"unread" | "all">("unread");
  const router = useRouter();

  const notificationOptions = useMemo(
    () => ({
      status: activeTab === "unread" ? NotificationStatus.DELIVERED : undefined,
      limit: 50,
    }),
    [activeTab],
  );

  const { notifications, loading, markAsRead, bulkMarkAsRead } =
    useNotifications(notificationOptions);

  const unreadCount = notifications.filter(
    (n) => n.status === NotificationStatus.DELIVERED,
  ).length;

  const handleMarkAsRead = async (notificationId: string) => {
    await markAsRead(notificationId);
  };

  const handleMarkAllAsRead = async () => {
    const unreadIds = notifications
      .filter((n) => n.status === NotificationStatus.DELIVERED)
      .map((n) => n.id);

    if (unreadIds.length > 0) {
      await bulkMarkAsRead(unreadIds);
    }
  };

  const filteredNotifications =
    activeTab === "unread"
      ? notifications.filter((n) => n.status === NotificationStatus.DELIVERED)
      : notifications;

  return (
    <div className={`relative ${className}`}>
      <Popover backdrop="blur">
        <PopoverTrigger>
          <div className="relative">
            <SidebarHeaderButton aria-label="Notifications">
              <NotificationIcon className="min-h-[20px] min-w-[20px] text-zinc-400 transition-all group-hover:text-primary" />
            </SidebarHeaderButton>
            {unreadCount > 0 && (
              <div className="absolute -right-1 bottom-3 flex h-full items-center justify-center">
                <div className="flex aspect-square h-4 w-4 items-center justify-center rounded-full bg-primary text-xs font-medium text-zinc-950">
                  {unreadCount > 99 ? "99+" : unreadCount}
                </div>
              </div>
            )}
          </div>
        </PopoverTrigger>

        <PopoverContent className="mr-4 w-96 rounded-2xl border-1 border-zinc-700 bg-zinc-800 p-0 shadow-xl">
          <Tabs
            selectedKey={activeTab}
            onSelectionChange={(key) => setActiveTab(key as "unread" | "all")}
            variant="underlined"
            fullWidth
          >
            <Tab
              key="unread"
              title={
                <div className="flex items-center gap-4">
                  <span>Unread</span>
                  {unreadCount > 0 && (
                    <Badge
                      className="border-0"
                      color="primary"
                      content={
                        unreadCount > 99 ? "99+" : unreadCount.toString()
                      }
                    >
                      <span />
                    </Badge>
                  )}
                </div>
              }
            />
            <Tab key="all" title={"All"} />
          </Tabs>

          {/* Notifications list */}
          <ScrollArea
            className={`${filteredNotifications.length === 0 ? "h-[30vh]" : "h-[70vh]"} w-full`}
          >
            {loading ? (
              <div className="flex items-center justify-center p-8">
                <div className="h-5 w-5 animate-spin rounded-full border-2 border-zinc-700 border-t-zinc-50" />
              </div>
            ) : filteredNotifications.length === 0 ? (
              <div className="flex h-full flex-col items-center justify-center p-8 text-center">
                <NotificationIcon className="mb-4 h-10 w-10 text-zinc-600" />
                <p className="font-medium text-zinc-300">
                  {activeTab === "unread"
                    ? "No unread notifications"
                    : "No notifications yet"}
                </p>
                <p className="mt-1 text-sm text-zinc-400">
                  {activeTab === "unread"
                    ? "All caught up!"
                    : "Notifications will appear here when you receive them"}
                </p>
              </div>
            ) : (
              <div className="w-full space-y-2 p-3">
                {filteredNotifications.map((notification) => (
                  <NotificationItem
                    key={notification.id}
                    notification={notification}
                    onMarkAsRead={handleMarkAsRead}
                  />
                ))}
              </div>
            )}
          </ScrollArea>

          {/* Footer */}
          <div className="flex w-full items-center justify-evenly gap-3 p-3">
            {unreadCount > 0 && (
              <Button size="sm" fullWidth onPress={handleMarkAllAsRead}>
                Mark all as read
              </Button>
            )}

            <Button
              fullWidth
              size="sm"
              variant={unreadCount > 0 ? "bordered" : "solid"}
              onPress={() => {
                router.push("/notifications");
              }}
            >
              View all notifications
            </Button>
          </div>
        </PopoverContent>
      </Popover>
    </div>
  );
}
