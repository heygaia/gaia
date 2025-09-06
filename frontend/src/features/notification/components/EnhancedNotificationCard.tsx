"use client";

import { Button as HeroButton } from "@heroui/button";
import { Tooltip } from "@heroui/react";
import { formatDistanceToNow } from "date-fns";
import {
  AlertCircle,
  CheckCheck,
  CheckCircle,
  Clock,
  ExternalLink,
} from "lucide-react";
import { useState } from "react";

import { ConfirmationDialog } from "@/components/shared/ConfirmationDialog";
import { useNotificationActions } from "@/hooks/useNotificationActions";
import {
  ActionType,
  ModalConfig,
  NotificationRecord,
  NotificationStatus,
} from "@/types/features/notificationTypes";
import { getNotificationIcon } from "@/utils/notifications";

import { Button } from "../../../components/ui";

interface EnhancedNotificationCardProps {
  notification: NotificationRecord;
  onMarkAsRead?: (id: string) => Promise<void>;
  onModalOpen?: (config: ModalConfig) => void;
  onRefresh?: () => void;
}

export const EnhancedNotificationCard = ({
  notification,
  onMarkAsRead,
  onModalOpen,
  onRefresh,
}: EnhancedNotificationCardProps) => {
  const [executingActionId, setExecutingActionId] = useState<string | null>(
    null,
  );

  const { executeAction, loading, getActionButtonProps, confirmationProps } =
    useNotificationActions({
      onSuccess: () => {
        // Refresh the notifications list if an action was successful
        onRefresh?.();
      },
      onModalOpen: (config) => {
        onModalOpen?.(config);
      },
    });

  const handleActionClick = async (actionId: string) => {
    const action = notification.content.actions?.find((a) => a.id === actionId);
    if (!action) return;

    setExecutingActionId(notification.id);
    try {
      await executeAction(notification.id, action);
    } finally {
      setExecutingActionId(null);
    }
  };

  const handleMarkAsRead = async () => {
    if (onMarkAsRead) {
      await onMarkAsRead(notification.id);
    }
  };

  const getActionIcon = (actionType: ActionType) => {
    switch (actionType) {
      case "redirect":
        return <ExternalLink className="h-3 w-3" />;
      case "api_call":
        return <CheckCircle className="h-3 w-3" />;
      case "workflow":
        return <Clock className="h-3 w-3" />;
      case "modal":
        return <AlertCircle className="h-3 w-3" />;
      default:
        return null;
    }
  };

  const timeAgo = formatDistanceToNow(new Date(notification.created_at), {
    addSuffix: true,
  });
  const isUnread = notification.status === NotificationStatus.DELIVERED;

  return (
    <div
      className={`w-full rounded-xl p-4 pb-1 transition-all duration-200 ${
        isUnread ? "bg-zinc-800" : "bg-zinc-800/70"
      }`}
    >
      <div className="flex items-start gap-3">
        <div className="mt-1 flex-shrink-0">
          {getNotificationIcon(notification.source)}
        </div>

        <div className="min-w-0 flex-1">
          <div className="flex items-start justify-between gap-4">
            <div className="flex-1">
              <div className="mb-1 flex items-center gap-2">
                <h3 className="text-sm font-medium text-white">
                  {notification.content.title}
                </h3>
                {isUnread && (
                  <div className="h-2 w-2 rounded-full bg-primary" />
                )}
              </div>
              <p className="text-sm whitespace-pre-line text-zinc-300">
                {notification.content.body}
              </p>
              <span className="flex-shrink-0 text-xs text-zinc-500">
                {timeAgo}
              </span>
            </div>

            {notification.status !== NotificationStatus.READ &&
              notification.status !== NotificationStatus.ARCHIVED && (
                <Tooltip content="Mark as Read">
                  <HeroButton
                    size="sm"
                    onPress={handleMarkAsRead}
                    variant={"flat"}
                    isIconOnly
                  >
                    <CheckCheck className="h-3.5 w-3.5" />
                  </HeroButton>
                </Tooltip>
              )}
          </div>

          {/* Actions */}
          <div className="mt-4 flex flex-wrap items-center gap-2">
            {notification?.content?.actions &&
              notification?.content?.actions.length > 0 &&
              notification.content?.actions.map((action) => {
                const buttonProps = getActionButtonProps(action);
                const isLoading =
                  loading === action.id || executingActionId === action.id;
                const isExecuted = action.executed || false;

                // Don't show loading for modal actions
                const showLoading = isLoading && action.type !== "modal";

                return (
                  <Button
                    key={action.id}
                    size="sm"
                    disabled={buttonProps.disabled || isLoading || isExecuted}
                    onClick={() => handleActionClick(action.id)}
                    className={`${
                      action.style === "primary"
                        ? "border-none bg-blue-600 text-white hover:bg-blue-700"
                        : action.style === "danger"
                          ? "border-none bg-red-600 text-white hover:bg-red-700"
                          : "border-none bg-zinc-700 text-white hover:bg-zinc-600"
                    } ${showLoading ? "opacity-50" : ""} ${
                      isExecuted ? "cursor-not-allowed opacity-50" : ""
                    }`}
                  >
                    {showLoading ? (
                      <div className="h-3 w-3 animate-spin rounded-full border-2 border-current border-t-transparent"></div>
                    ) : (
                      <>
                        {action.label}
                        {isExecuted && <span className="ml-1">✓</span>}
                        {!isExecuted && getActionIcon(action.type)}
                      </>
                    )}
                  </Button>
                );
              })}
          </div>
        </div>
      </div>

      {/* Confirmation Dialog */}
      <ConfirmationDialog {...confirmationProps} />
    </div>
  );
};
