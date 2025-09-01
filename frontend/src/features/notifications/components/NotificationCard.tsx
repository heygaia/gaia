import { Button } from "@heroui/button";
import { Card, CardBody, CardFooter, CardHeader } from "@heroui/card";
import { Chip } from "@heroui/chip";
import {
  CheckIcon,
  ClockIcon,
  InfoIcon,
  AlertTriangleIcon,
  XCircleIcon,
} from "lucide-react";
import React from "react";
import { toast } from "sonner";

import {
  NotificationRecord,
  NotificationStatus,
  NotificationType,
} from "@/types/features/notificationTypes";

interface NotificationCardProps {
  notification: NotificationRecord;
  onMarkAsRead?: (notificationId: string) => void;
  onExecuteAction?: (notificationId: string, actionId: string) => void;
  onArchive?: (notificationId: string) => void;
}

const getNotificationIcon = (type: NotificationType) => {
  switch (type) {
    case NotificationType.SUCCESS:
      return <CheckIcon className="h-4 w-4 text-success" />;
    case NotificationType.WARNING:
      return <AlertTriangleIcon className="h-4 w-4 text-warning" />;
    case NotificationType.ERROR:
      return <XCircleIcon className="h-4 w-4 text-danger" />;
    default:
      return <InfoIcon className="h-4 w-4 text-primary" />;
  }
};

const getStatusColor = (status: NotificationStatus) => {
  switch (status) {
    case NotificationStatus.READ:
      return "success";
    case NotificationStatus.PENDING:
      return "warning";
    case NotificationStatus.ARCHIVED:
      return "default";
    default:
      return "primary";
  }
};

const formatDate = (dateString: string) => {
  const date = new Date(dateString);
  const now = new Date();
  const diffInMs = now.getTime() - date.getTime();
  const diffInHours = diffInMs / (1000 * 60 * 60);
  const diffInDays = diffInHours / 24;

  if (diffInHours < 1) {
    const diffInMinutes = Math.floor(diffInMs / (1000 * 60));
    return `${diffInMinutes}m ago`;
  } else if (diffInHours < 24) {
    return `${Math.floor(diffInHours)}h ago`;
  } else if (diffInDays < 7) {
    return `${Math.floor(diffInDays)}d ago`;
  } else {
    return date.toLocaleDateString();
  }
};

export default function NotificationCard({
  notification,
  onMarkAsRead,
  onExecuteAction,
  onArchive,
}: NotificationCardProps) {
  const { content, source } = notification;
  const { status, created_at } = notification;

  // Try to infer type from content or use default
  const getNotificationType = (): NotificationType => {
    // If there's metadata that contains type information
    if (notification.metadata && "type" in notification.metadata) {
      const metaType = notification.metadata.type as string;
      if (
        Object.values(NotificationType).includes(metaType as NotificationType)
      ) {
        return metaType as NotificationType;
      }
    }

    // Default based on content or source
    if (
      content.title.toLowerCase().includes("error") ||
      content.body.toLowerCase().includes("error")
    ) {
      return NotificationType.ERROR;
    }
    if (
      content.title.toLowerCase().includes("warning") ||
      content.body.toLowerCase().includes("warning")
    ) {
      return NotificationType.WARNING;
    }
    if (
      content.title.toLowerCase().includes("success") ||
      content.body.toLowerCase().includes("complete")
    ) {
      return NotificationType.SUCCESS;
    }

    return NotificationType.INFO;
  };

  const type = getNotificationType();

  const handleMarkAsRead = () => {
    if (onMarkAsRead && status !== NotificationStatus.READ) {
      onMarkAsRead(notification.id);
      toast.success("Notification marked as read");
    }
  };

  const handleExecuteAction = (actionId: string) => {
    if (onExecuteAction) {
      onExecuteAction(notification.id, actionId);
    }
  };

  const handleArchive = () => {
    if (onArchive) {
      onArchive(notification.id);
      toast.success("Notification archived");
    }
  };

  return (
    <Card
      className={`w-full ${status === NotificationStatus.READ ? "opacity-60" : ""}`}
      shadow="sm"
    >
      <CardHeader className="flex flex-row items-start justify-between pb-2">
        <div className="flex flex-1 items-start gap-2">
          {getNotificationIcon(type)}
          <div className="flex-1">
            <div className="mb-1 flex items-center gap-2">
              <h4 className="text-sm font-semibold text-foreground">
                {content.title}
              </h4>
              <Chip size="sm" color={getStatusColor(status)} variant="flat">
                {status}
              </Chip>
            </div>
            <div className="flex items-center gap-2 text-xs text-foreground-500">
              <span className="capitalize">{source.replace("_", " ")}</span>
              <span>•</span>
              <span className="flex items-center gap-1">
                <ClockIcon className="h-3 w-3" />
                {formatDate(created_at)}
              </span>
            </div>
          </div>
        </div>
      </CardHeader>

      <CardBody className="pt-0">
        <p className="text-sm leading-relaxed text-foreground-700">
          {content.body}
        </p>

        {/* Rich content display */}
        {content.rich_content && (
          <div className="mt-3 space-y-2">
            {content.rich_content.images && (
              <div className="flex flex-wrap gap-2">
                {content.rich_content.images.map(
                  (image: any, index: number) => (
                    <img
                      key={index}
                      src={image.url}
                      alt={image.alt || "Notification image"}
                      className="h-20 w-20 rounded-md object-cover"
                    />
                  ),
                )}
              </div>
            )}
          </div>
        )}
      </CardBody>

      {/* Actions */}
      {(content.actions?.length || status !== NotificationStatus.READ) && (
        <CardFooter className="flex flex-wrap gap-2 pt-0">
          {content.actions?.map((action: any) => (
            <Button
              key={action.id}
              size="sm"
              color={
                action.style === "primary"
                  ? "primary"
                  : action.style === "danger"
                    ? "danger"
                    : "default"
              }
              variant={action.style === "primary" ? "solid" : "bordered"}
              onPress={() => handleExecuteAction(action.id)}
              disabled={action.disabled || action.executed}
              startContent={
                action.icon && <span className="text-xs">{action.icon}</span>
              }
            >
              {action.label}
            </Button>
          ))}

          {/* Default actions */}
          {status !== NotificationStatus.READ && (
            <Button size="sm" variant="light" onPress={handleMarkAsRead}>
              Mark as read
            </Button>
          )}

          {status !== NotificationStatus.ARCHIVED && (
            <Button size="sm" variant="light" onPress={handleArchive}>
              Archive
            </Button>
          )}
        </CardFooter>
      )}
    </Card>
  );
}
