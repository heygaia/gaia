import SettingsMenu from "@/components/layout/sidebar/settings/SettingsMenu";
import { useUser } from "@/features/auth/hooks/useUser";

import { Avatar, AvatarFallback, AvatarImage } from "../../ui/shadcn/avatar";
// import Spinner from "@/components/ui/spinner";

export default function UserContainer() {
  const user = useUser();

  return (
    <div className="pointer-events-auto relative flex w-full flex-col justify-center gap-3 bg-transparent">
      <div className="user_container_inner rounded-xl bg-zinc-900 px-3">
        <div className="flex items-center gap-2">
          <Avatar className="size-7 rounded-full bg-black">
            <AvatarImage
              src={
                user?.profilePicture ||
                "https://links.aryanranderiya.com/l/default_user"
              }
              alt="Avatar"
            />
            <AvatarFallback>User</AvatarFallback>
          </Avatar>
          <span className="text-sm">{user?.name}</span>
        </div>

        <SettingsMenu />
      </div>
    </div>
  );
}
