import Image from "next/image";
import Link from "next/link";
import { ReactNode } from "react";

import { SidebarHeaderButton } from "@/components";
import ContactSupport from "@/components/layout/sidebar/ContactSupport";
import SidebarTopButtons from "@/components/layout/sidebar/SidebarTopButtons";
import UserContainer from "@/components/layout/sidebar/UserContainer";
import {
  SidebarLeft01Icon,
  SidebarRight01Icon,
} from "@/components/shared/icons";
import { Button } from "@/components/ui/shadcn/button";
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarGroupContent,
  SidebarHeader,
  useSidebar,
} from "@/components/ui/shadcn/sidebar";

interface SidebarLayoutProps {
  children: ReactNode;
}

// Custom SidebarTrigger with dynamic icons
export const CustomSidebarTrigger = () => {
  const { open, toggleSidebar } = useSidebar();

  return (
    <SidebarHeaderButton
      onClick={toggleSidebar}
      aria-label="Toggle Sidebar"
      tooltip={open ? "Collapse Sidebar" : "Open Sidebar"}
    >
      {open ? (
        <SidebarLeft01Icon
          className="max-h-5 min-h-5 max-w-5 min-w-5 text-zinc-400 transition group-hover/btn:text-primary"
          color={undefined}
        />
      ) : (
        <SidebarRight01Icon
          className="max-h-5 min-h-5 max-w-5 min-w-5 text-zinc-400 transition group-hover/btn:text-primary"
          color={undefined}
        />
      )}
    </SidebarHeaderButton>
  );
};

export default function SidebarLayout({ children }: SidebarLayoutProps) {
  return (
    <Sidebar
      variant="sidebar"
      collapsible="offcanvas"
      className="sidebar border-none!"
    >
      <SidebarHeader className="pb-0">
        <div className="flex items-center justify-between">
          <Link href={"/"}>
            <Button className="group flex items-center gap-2 rounded-full bg-transparent px-2 hover:bg-foreground/10">
              <Image
                alt="GAIA Logo"
                src="/images/logos/logo.webp"
                width={23}
                height={23}
              />
            </Button>
          </Link>
          <CustomSidebarTrigger />
        </div>
      </SidebarHeader>

      <SidebarContent className="flex-1 px-1">
        <SidebarGroup>
          <SidebarGroupContent className="space-y-1 overflow-hidden">
            <SidebarTopButtons />
            {children}
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>

      <SidebarFooter className="relative z-[4] p-2 px-3 pb-3">
        <ContactSupport />
        <UserContainer />
      </SidebarFooter>
    </Sidebar>
  );
}
