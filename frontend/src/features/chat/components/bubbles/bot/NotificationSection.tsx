import React from "react";

import NotificationCard from "@/features/notifications/components/NotificationCard";
import { NotificationRecord } from "@/types/features/notificationTypes";

interface NotificationSectionProps {
  notification_data: NotificationRecord[];
}

export default function NotificationSection({
  notification_data,
}: NotificationSectionProps) {
  const handleMarkAsRead = (notificationId: string) => {
    // This will be handled by the parent component or global state
    console.log("Mark as read:", notificationId);
  };

  const handleExecuteAction = (notificationId: string, actionId: string) => {
    // This will trigger the corresponding action
    console.log("Execute action:", { notificationId, actionId });
  };

  const handleArchive = (notificationId: string) => {
    // This will archive the notification
    console.log("Archive notification:", notificationId);
  };

  // Handle empty state
  if (!notification_data || notification_data.length === 0) {
    return (
      <div className="mt-3 w-full py-4 text-center text-sm text-foreground-500">
        No notifications to display
      </div>
    );
  }

  return (
    <div className="mt-3 w-full space-y-3">
      {notification_data.map((notification, index) => (
        <NotificationCard
          key={notification.id || index}
          notification={notification}
          onMarkAsRead={handleMarkAsRead}
          onExecuteAction={handleExecuteAction}
          onArchive={handleArchive}
        />
      ))}
    </div>
  );
}
