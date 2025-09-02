import { Search } from "lucide-react";
import Image from "next/image";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { ReactNode, useState } from "react";

import { SidebarHeaderButton } from "@/components";
import ContactSupport from "@/components/layout/sidebar/ContactSupport";
import SidebarTopButtons from "@/components/layout/sidebar/SidebarTopButtons";
import UserContainer from "@/components/layout/sidebar/UserContainer";
import {
  ChatBubbleAddIcon,
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
import SearchCommand from "@/features/search/components/SearchCommand";

interface SidebarLayoutProps {
  children: ReactNode;
}

// Custom SidebarTrigger with dynamic icons
const CustomSidebarTrigger = () => {
  const { open, toggleSidebar } = useSidebar();

  return (
    <SidebarHeaderButton onClick={toggleSidebar} aria-label="Toggle Sidebar">
      {open ? (
        <SidebarLeft01Icon className="max-h-5 min-h-5 max-w-5 min-w-5" />
      ) : (
        <SidebarRight01Icon className="max-h-5 min-h-5 max-w-5 min-w-5" />
      )}
    </SidebarHeaderButton>
  );
};

export default function SidebarLayout({ children }: SidebarLayoutProps) {
  const router = useRouter();
  const pathname = usePathname();
  const [openSearchDialog, setOpenSearchDialog] = useState(false);

  return (
    <Sidebar
      variant="sidebar"
      collapsible="offcanvas"
      className="sidebar border-none!"
    >
      {pathname.startsWith("/c") && (
        <div className="pointer-events-none absolute right-0 bottom-26 left-0 z-1 h-1/4 w-full bg-gradient-to-b from-transparent to-[#141414]" />
      )}

      <SearchCommand
        openSearchDialog={openSearchDialog}
        setOpenSearchDialog={setOpenSearchDialog}
      />

      <SidebarHeader className="pb-0">
        <div className="flex items-center justify-between">
          <Link href={"/"}>
            <Button className="group flex items-center gap-2 rounded-full bg-transparent px-2 hover:bg-foreground/10">
              <Image
                alt="GAIA Logo"
                src="/branding/logo.webp"
                width={23}
                height={23}
              />
            </Button>
          </Link>

          <div className="flex items-center gap-1">
            <SidebarHeaderButton
              onClick={() => setOpenSearchDialog(true)}
              aria-label="Search"
            >
              <Search className="max-h-5 min-h-5 max-w-5 min-w-5" />
            </SidebarHeaderButton>
            {!pathname.startsWith("/c") && (
              <SidebarHeaderButton
                onClick={() => router.push("/c")}
                aria-label="New chat"
              >
                <ChatBubbleAddIcon
                  className="max-h-5 min-h-5 max-w-5 min-w-5"
                  color={undefined}
                />
              </SidebarHeaderButton>
            )}
            <CustomSidebarTrigger />
          </div>
        </div>
      </SidebarHeader>

      <SidebarContent className="flex-1">
        <SidebarGroup>
          <SidebarGroupContent className="space-y-1 overflow-hidden">
            <SidebarTopButtons />

            {children}
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>

      <SidebarFooter className="relative z-[4] p-2">
        <ContactSupport />
        <UserContainer />
      </SidebarFooter>
    </Sidebar>
  );
}
