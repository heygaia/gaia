"use client";

import { Button } from "@heroui/button";
import { CircleArrowUp, ZapIcon } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import React, { useEffect, useState } from "react";

import {
  CalendarIcon,
  CheckmarkCircle02Icon,
  MessageMultiple02Icon,
  NotificationIcon,
  Target04Icon,
} from "@/components/shared/icons";
import { useNotifications } from "@/features/notification/hooks/useNotifications";
import { useUserSubscriptionStatus } from "@/features/pricing/hooks/usePricing";
import { useRefreshTrigger } from "@/stores/notificationStore";
import { NotificationStatus } from "@/types/features/notificationTypes";

export default function SidebarTopButtons() {
  const pathname = usePathname();
  const { data: subscriptionStatus } = useUserSubscriptionStatus();
  const refreshTrigger = useRefreshTrigger();
  const { notifications, refetch } = useNotifications({
    status: NotificationStatus.DELIVERED,
    limit: 50,
  });

  const [unreadCount, setUnreadCount] = useState(0);

  useEffect(() => {
    refetch();
  }, [refreshTrigger, refetch]);

  useEffect(() => {
    setUnreadCount(
      notifications.filter((n) => n.status !== NotificationStatus.READ).length,
    );
  }, [notifications]);

  const buttonData = [
    {
      route: "/notifications",
      icon: <NotificationIcon />,
      label: "Notifications",
    },
    {
      route: "/calendar",
      icon: <CalendarIcon />,
      label: "Calendar",
    },
    {
      route: "/goals",
      icon: <Target04Icon />,
      label: "Goals",
    },
    {
      route: "/todos",
      icon: <CheckmarkCircle02Icon />,
      label: "Todos",
    },
    // {
    //   route: "/mail",
    //   icon: <Mail01Icon />,
    //   label: "Mail",
    // },
    {
      route: "/workflows",
      icon: <ZapIcon />,
      label: "Workflows",
    },
    {
      route: "/c",
      icon: <MessageMultiple02Icon />,
      label: "Chats",
    },

    // {
    //   route: "/browser",
    //   icon: <AiBrowserIcon height={23} width={23} />,
    //   label: "Use Browser",
    // },
  ];

  return (
    <div className="flex flex-col">
      {/* Only show Upgrade to Pro button when user doesn't have an active subscription */}
      {!subscriptionStatus?.is_subscribed && (
        <Link href={"/pricing"}>
          <Button
            variant="faded"
            className="mb-2 flex h-fit w-full justify-start gap-3 px-3"
          >
            <CircleArrowUp width={20} height={20} />
            <div className="flex items-center gap-4">
              <div className="flex w-full flex-col justify-center py-2">
                <div className="text-left text-sm font-medium">
                  Upgrade to Pro
                </div>
                <div className="line-clamp-2 text-left text-xs font-light text-wrap text-foreground-500">
                  All features & unlimited usage
                </div>
              </div>
            </div>
          </Button>
        </Link>
      )}

      <div className="mb-3 flex flex-col gap-0.5">
        {/* <div className="w-full px-2 pt-0 pb-1 text-xs font-medium text-foreground-400">
          Menu
        </div> */}
        {buttonData.map(({ route, icon, label }, index) => (
          <div key={index} className="relative">
            <Button
              className="w-full justify-start text-sm"
              size="sm"
              as={Link}
              href={route}
              variant="light"
              color={
                route === "/c"
                  ? pathname === "/c" || pathname.startsWith("/c/")
                    ? "primary"
                    : "default"
                  : pathname === route
                    ? "primary"
                    : "default"
              }
              // onPress={() => handleButtonPress(route)}
              startContent={React.cloneElement(icon, {
                color:
                  route === "/c"
                    ? pathname === "/c" || pathname.startsWith("/c/")
                      ? "#00bbff"
                      : "#9b9b9b"
                    : pathname === route
                      ? "#00bbff"
                      : "#9b9b9b",
                width: 18,
                height: 18,
              })}
            >
              {label}
            </Button>
            {/* Show unread badge for notifications */}
            {route === "/notifications" && unreadCount > 0 && (
              <div className="absolute top-0 right-2 flex h-full items-center justify-center">
                <div className="flex aspect-square h-4 w-4 items-center justify-center rounded-full bg-primary text-xs font-medium text-zinc-950">
                  {unreadCount > 99 ? "9+" : unreadCount}
                </div>
              </div>
            )}
          </div>
        ))}
      </div>

      {/* <Button
        className="flex w-full justify-start text-sm"
        size="sm"
        variant="light"
        color={
          pathname == "/c" || pathname.startsWith("/c/") ? "primary" : "default"
        }
        onPress={createNewChat}
        startContent={
          <ChatBubbleAddIcon
            color={
              pathname == "/c" || pathname.startsWith("/c/")
                ? "#00bbff"
                : "#9b9b9b"
            }
            width={19}
            height={19}
          />
        }
      >
        New Chat
      </Button> */}

      {/*
      <div className="my-3 mt-1 px-1">
        <Separator className="bg-zinc-800" />
      </div> */}
    </div>
  );
}
