"use client";

import {
  SwipeableList,
  SwipeableListItem,
  Type as ListType,
} from "react-swipeable-list";

import { Notification } from "@/types/notifications";

import {
  NotificationLeadingActions,
  NotificationTrailingActions,
} from "./NotificationActions";
import { NotificationCard } from "./NotificationCard";

interface SwipeableNotificationProps {
  notification: Notification;
  onAction: (
    notification: Notification,
    actionType: string,
    actionId?: string,
  ) => void;
}

export const SwipeableNotification = ({
  notification,
  onAction,
}: SwipeableNotificationProps) => {
  return (
    <SwipeableList threshold={0.5} type={ListType.IOS}>
      <SwipeableListItem
        leadingActions={
          <NotificationLeadingActions
            notification={notification}
            onAction={onAction}
          />
        }
        trailingActions={
          <NotificationTrailingActions
            notification={notification}
            onAction={onAction}
          />
        }
      >
        <NotificationCard notification={notification} onAction={onAction} />
      </SwipeableListItem>
    </SwipeableList>
  );
};
