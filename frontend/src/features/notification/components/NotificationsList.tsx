"use client";

import { Spinner } from "@heroui/react";
import { useMemo } from "react";

import {
  ModalConfig,
  NotificationRecord,
} from "@/types/features/notificationTypes";
import { groupNotificationsByTimezone } from "@/utils";

import { NotificationIcon } from "../../../components/shared/icons";
import { EnhancedNotificationCard } from "./EnhancedNotificationCard";

interface NotificationListProps {
  notifications: NotificationRecord[];
  loading: boolean;
  emptyMessage?: string;
  emptyDescription?: string;
  onRefresh?: () => void;
  onMarkAsRead: (notificationId: string) => Promise<void>;
  onModalOpen?: (config: ModalConfig) => void;
}

export const NotificationsList = ({
  notifications,
  loading,
  emptyMessage = "No notifications",
  emptyDescription = "Notifications will appear here when you receive them.",
  onRefresh,
  onMarkAsRead,
  onModalOpen,
}: NotificationListProps) => {
  const groupedNotifications = useMemo(
    () => groupNotificationsByTimezone(notifications),
    [notifications],
  );

  const handleMarkAsRead = async (notificationId: string) => {
    try {
      // Only call the provided onMarkAsRead function - don't trigger additional refreshes here
      await onMarkAsRead(notificationId);
    } catch (error) {
      console.error("Error in handleMarkAsRead:", error);
    }
  };

  if (loading) {
    return (
      <div className="mx-auto flex min-h-screen w-full max-w-4xl items-center justify-center text-white">
        <div className="flex flex-col items-center space-y-4">
          <Spinner />
        </div>
      </div>
    );
  }

  if (notifications.length === 0) {
    return (
      <div className="mx-auto flex h-[70vh] w-full max-w-4xl items-center justify-center text-white">
        <div className="flex flex-col items-center space-y-4 text-center">
          <div className="flex h-12 w-12 items-center justify-center rounded-full bg-zinc-800">
            <span className="text-2xl">
              <NotificationIcon />
            </span>
          </div>
          <div>
            <h3 className="text-lg font-medium text-white">{emptyMessage}</h3>
            <p className="text-sm text-zinc-400">{emptyDescription}</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="mx-auto min-h-screen w-full max-w-4xl overflow-y-auto pb-14 text-white">
      <div className="space-y-6 p-4">
        {Object.entries(groupedNotifications).map(
          ([timeGroup, groupNotifications]) => (
            <div key={timeGroup} className="space-y-4">
              <h3 className="text-sm font-medium text-zinc-400">{timeGroup}</h3>
              <div className="space-y-3">
                {groupNotifications.map((notification) => (
                  <EnhancedNotificationCard
                    key={notification.id}
                    notification={notification}
                    onMarkAsRead={handleMarkAsRead}
                    onRefresh={onRefresh}
                    onModalOpen={onModalOpen}
                  />
                ))}
              </div>
            </div>
          ),
        )}
      </div>
    </div>
  );
};
