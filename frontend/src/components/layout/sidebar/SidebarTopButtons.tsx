"use client";

import { Button } from "@heroui/button";
import { CircleArrowUp } from "lucide-react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import React from "react";

import {
  CalendarIcon,
  ChatBubbleAddIcon,
  CheckmarkCircle02Icon,
  Mail01Icon,
  NotificationIcon,
  PinIcon,
  Route02Icon,
} from "@/components/shared/icons";
import { Separator } from "@/components/ui";
import { useConversation } from "@/features/chat/hooks/useConversation";
import { useNotifications } from "@/features/notification/hooks/useNotifications";
import { useUserSubscriptionStatus } from "@/features/pricing/hooks/usePricing";
import { NotificationStatus } from "@/types/features/notificationTypes";

export default function SidebarTopButtons() {
  const router = useRouter();
  const pathname = usePathname();
  const { clearMessages } = useConversation();
  const { data: subscriptionStatus } = useUserSubscriptionStatus();

  // Get unread notifications count
  const { notifications } = useNotifications({
    status: NotificationStatus.DELIVERED,
    limit: 50,
  });

  const unreadCount = notifications.filter(
    (n) => n.status === NotificationStatus.DELIVERED,
  ).length;

  const buttonData = [
    {
      route: "/notifications",
      icon: <NotificationIcon width={19} height={19} />,
      label: "Notifications",
    },
    {
      route: "/calendar",
      icon: <CalendarIcon width={19} height={19} />,
      label: "Calendar",
    },
    {
      route: "/goals",
      icon: <Route02Icon width={19} height={19} />,
      label: "Goals",
    },
    {
      route: "/todos",
      icon: <CheckmarkCircle02Icon width={19} height={19} />,
      label: "Todos",
    },
    {
      route: "/mail",
      icon: <Mail01Icon width={19} height={19} />,
      label: "Mail",
    },
    {
      route: "/pins",
      icon: <PinIcon width={19} height={19} />,
      label: "Pins",
    },

    // {
    //   route: "/browser",
    //   icon: <AiBrowserIcon height={23} width={23} />,
    //   label: "Use Browser",
    // },
  ];

  const createNewChat = (): void => {
    router.push(`/c`);
    clearMessages();
  };

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

      <div className="flex flex-col gap-0.5">
        {buttonData.map(({ route, icon, label }, index) => (
          <div key={index} className="relative">
            <Button
              className="w-full justify-start text-sm"
              size="sm"
              variant="light"
              color={pathname === route ? "primary" : "default"}
              onPress={() => router.push(route)}
              startContent={React.cloneElement(icon, {
                color: pathname === route ? "#00bbff" : "#9b9b9b",
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

      <Button
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
      </Button>

      <div className="my-2 px-3">
        <Separator className="bg-zinc-800" />
      </div>
    </div>
  );
}
