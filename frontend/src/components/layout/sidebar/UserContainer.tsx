import Image from "next/image";

import SettingsMenu from "@/components/layout/sidebar/settings/SettingsMenu";
import { useUser } from "@/features/auth/hooks/useUser";
import { useUserSubscriptionStatus } from "@/features/pricing/hooks/usePricing";

import { Avatar, AvatarFallback, AvatarImage } from "../../ui/shadcn/avatar";

export default function UserContainer() {
  const user = useUser();
  const { data: subscriptionStatus } = useUserSubscriptionStatus();

  return (
    <div className="pointer-events-auto relative flex w-full flex-col justify-center gap-3 bg-transparent">
      <div className="user_container_inner rounded-xl bg-transparent px-2">
        <div className="flex items-center gap-3">
          <Avatar className="size-7 rounded-full bg-black">
            <AvatarImage src={user?.profilePicture} alt="User Avatar" />
            <AvatarFallback>
              <Image
                src={"/media/default.webp"}
                width={30}
                height={30}
                alt="Default profile picture"
              />
            </AvatarFallback>
          </Avatar>
          <div className="flex flex-col -space-y-0.5">
            <span className="text-sm">{user?.name}</span>
            <span className="text-[11px] text-foreground-400">
              {subscriptionStatus?.is_subscribed
                ? "GAIA Pro"
                : "GAIA Free Tier"}
            </span>
          </div>
        </div>

        <SettingsMenu />
      </div>
    </div>
  );
}
