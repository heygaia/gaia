"use client";

import { Tab, Tabs } from "@heroui/react";
import { Bell, BellRing } from "lucide-react";
import { useState } from "react";

import { EmailPreviewModal } from "@/components/Modals/EmailPreviewModal";
import { NotificationsList } from "@/components/Notifications/NotificationsList";
import { useAllNotifications } from "@/features/notification/hooks/useAllNotifications";
import { useNotifications } from "@/features/notification/hooks/useNotifications";
import { NotificationsAPI } from "@/services/api/notifications";
import {
  ModalConfig,
  NotificationStatus,
} from "@/types/features/notificationTypes";

export default function NotificationsPage() {
  const [modalConfig, setModalConfig] = useState<ModalConfig | null>(null);

  // Get unread notifications
  const {
    notifications: unreadNotifications,
    loading: unreadLoading,
    refetch: refetchUnread,
  } = useNotifications({
    status: NotificationStatus.DELIVERED,
    limit: 100,
    channel_type: "inapp",
  });

  // Get all notifications data
  const {
    allNotifications,
    loading: allLoading,
    refetchAll,
  } = useAllNotifications({
    limit: 100,
    channel_type: "inapp",
  });

  // Simple mark as read that refreshes both lists
  const handleMarkAsRead = async (notificationId: string) => {
    try {
      await NotificationsAPI.markAsRead(notificationId);
      // Refresh both lists after marking as read
      await refetchUnread();
      await refetchAll();
    } catch (error) {
      console.error("Error marking notification as read:", error);
    }
  };

  // Simple refresh function
  const refreshNotifications = async () => {
    await refetchAll();
    await refetchUnread();
  };

  // Handle modal opening from notification actions
  const handleModalOpen = (config: ModalConfig) => {
    setModalConfig(config);
  };

  // Handle modal closing
  const handleModalClose = () => {
    setModalConfig(null);
  };

  // Handle email sent callback to refresh notifications
  const handleEmailSent = () => {
    // Refresh notifications after email is sent
    refreshNotifications();
  };

  return (
    <div className="flex w-full flex-col items-center justify-center overflow-y-auto p-5">
      <Tabs
        aria-label="Notifications"
        color="primary"
        variant="underlined"
        className="flex w-full justify-center"
        classNames={{
          base: "w-full",
          tabList: "w-full max-w-4xl px-0",
          panel: "overflow-y-scroll",
        }}
      >
        <Tab
          key="unread"
          className="w-full"
          title={
            <div className="flex items-center space-x-2">
              <BellRing className="h-4 w-4" />
              <span>Unread</span>
              {unreadNotifications.length != 0 && (
                <span className="my-2 flex aspect-square items-center rounded-full bg-zinc-600 px-2 text-xs text-foreground">
                  {unreadNotifications.length}
                </span>
              )}
            </div>
          }
        >
          <NotificationsList
            notifications={unreadNotifications}
            loading={unreadLoading}
            emptyMessage="No unread notifications"
            emptyDescription="All caught up! You're up to date with everything."
            onRefresh={refreshNotifications}
            onMarkAsRead={handleMarkAsRead}
            onModalOpen={handleModalOpen}
          />
        </Tab>
        <Tab
          className="w-full"
          key="all"
          title={
            <div className="flex items-center space-x-2">
              <Bell className="h-4 w-4" />
              <span>All</span>
            </div>
          }
        >
          <NotificationsList
            notifications={allNotifications}
            loading={allLoading}
            emptyMessage="No notifications yet"
            emptyDescription="Notifications will appear here when you receive them."
            onRefresh={refreshNotifications}
            onMarkAsRead={handleMarkAsRead}
            onModalOpen={handleModalOpen}
          />
        </Tab>
      </Tabs>

      {/* Email Preview Modal */}
      {modalConfig?.component === "EmailPreviewModal" && modalConfig.props && (
        <EmailPreviewModal
          isOpen={true}
          onClose={handleModalClose}
          email_id={modalConfig.props.email_id || ""}
          subject={modalConfig.props.subject || ""}
          body={modalConfig.props.body || ""}
          recipients={modalConfig.props.recipients || []}
          mode={modalConfig.props.mode === "view" ? "view" : "edit"}
          onEmailSent={handleEmailSent}
          notificationId={modalConfig.props.notificationId}
          actionId={modalConfig.props.actionId}
        />
      )}
    </div>
  );
}
