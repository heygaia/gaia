"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
} from "react";

import { useNotifications } from "@/features/notification/hooks/useNotifications";
import { NotificationStatus } from "@/types/features/notificationTypes";

interface NotificationContextType {
  refreshTrigger: number;
  triggerRefresh: () => void;
  unreadCount: number;
  markAsRead: (id: string) => Promise<void>;
  bulkMarkAsRead: (ids: string[]) => Promise<void>;
}

const NotificationContext = createContext<NotificationContextType | undefined>(
  undefined,
);

export const NotificationProvider = ({
  children,
}: {
  children: React.ReactNode;
}) => {
  const [refreshTrigger, setRefreshTrigger] = useState(0);

  const { notifications, markAsRead, bulkMarkAsRead, refetch } =
    useNotifications({
      status: NotificationStatus.DELIVERED,
      limit: 50,
    });

  const unreadCount = notifications.filter(
    (n) => n.status === NotificationStatus.DELIVERED,
  ).length;

  const triggerRefresh = useCallback(() => {
    setRefreshTrigger((prev) => prev + 1);
    refetch();
  }, [refetch]);

  useEffect(() => {
    refetch();
  }, [refreshTrigger, refetch]);

  const handleMarkAsRead = useCallback(
    async (id: string) => {
      await markAsRead(id);
      triggerRefresh();
    },
    [markAsRead, triggerRefresh],
  );

  const handleBulkMarkAsRead = useCallback(
    async (ids: string[]) => {
      await bulkMarkAsRead(ids);
      triggerRefresh();
    },
    [bulkMarkAsRead, triggerRefresh],
  );

  return (
    <NotificationContext.Provider
      value={{
        refreshTrigger,
        triggerRefresh,
        unreadCount,
        markAsRead: handleMarkAsRead,
        bulkMarkAsRead: handleBulkMarkAsRead,
      }}
    >
      {children}
    </NotificationContext.Provider>
  );
};

export const useNotificationContext = () => {
  const context = useContext(NotificationContext);
  if (context === undefined) {
    throw new Error(
      "useNotificationContext must be used within a NotificationProvider",
    );
  }
  return context;
};
