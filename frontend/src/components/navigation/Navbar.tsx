"use client";

import { Button } from "@heroui/button";
import { motion } from "framer-motion";
import { ChevronDown } from "lucide-react";
import Image from "next/image";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";

import MobileMenu from "@/components/navigation/MobileMenu";
import { LinkButton } from "@/components/shared/LinkButton";
import { appConfig } from "@/config/appConfig";
import { useUser } from "@/features/auth/hooks/useUser";
import useMediaQuery from "@/hooks/ui/useMediaQuery";

import { BubbleConversationChatIcon } from "../shared";
import { NavbarMenu } from "./NavbarMenu";
import { RainbowGithubButton } from "./RainbowGithubButton";

export default function Navbar() {
  const pathname = usePathname();
  const isMobileScreen = useMediaQuery("(max-width: 990px)");
  const [activeDropdown, setActiveDropdown] = useState<string | null>(null);
  const [hoveredItem, setHoveredItem] = useState<string | null>(null);

  const user = useUser();

  // Function to control backdrop blur
  const toggleBackdrop = (show: boolean) => {
    const backdrop = document.getElementById("navbar-backdrop");
    if (backdrop) {
      if (show) {
        backdrop.style.opacity = "1";
        backdrop.style.pointerEvents = "none";
      } else {
        backdrop.style.opacity = "0";
        backdrop.style.pointerEvents = "none";
      }
    }
  };

  // Handle mouse leave for navbar container
  const handleNavbarMouseLeave = () => {
    if (!isMobileScreen) {
      setActiveDropdown(null);
      setHoveredItem(null);
      toggleBackdrop(false);
    }
  };

  const handleMouseEnter = (menu: string) => {
    if (!isMobileScreen) {
      setActiveDropdown(menu);
      setHoveredItem(menu);
      toggleBackdrop(true);
    }
  };

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      toggleBackdrop(false);
    };
  }, []);

  return (
    <div className="fixed top-0 left-0 z-50 w-full px-4 pt-4">
      <div
        className="relative mx-auto max-w-5xl"
        onMouseLeave={handleNavbarMouseLeave}
      >
        <div
          className={`navbar_content flex h-14 w-full items-center justify-between bg-[#ffffff10] px-3 backdrop-blur-xl transition-all duration-300 ${
            activeDropdown ? "rounded-t-2xl bg-[#08090A]" : "rounded-2xl"
          }`}
          style={activeDropdown ? { backgroundColor: "#08090A" } : {}}
        >
          <Button
            as={Link}
            radius="full"
            href={"/"}
            variant="light"
            isIconOnly
            className="h-10 w-10"
          >
            <Image
              src="/branding/logo.webp"
              alt="GAIA Logo"
              width={30}
              height={30}
            />
          </Button>

          <div className="hidden items-center gap-1 sm:flex">
            {appConfig.links.main
              .filter((link) => link.href !== "/") // Filter out Home link for desktop nav
              .map(({ href, label, icon, external }) => (
                <LinkButton
                  key={href}
                  size="sm"
                  className={`text-sm font-medium ${
                    pathname === href
                      ? "text-primary"
                      : "text-zinc-400 hover:text-zinc-300"
                  }`}
                  as={Link}
                  href={href}
                  startContent={icon}
                  external={external}
                >
                  {label}
                </LinkButton>
              ))}
          </div>

          {isMobileScreen ? (
            <MobileMenu />
          ) : (
            <div className="flex items-center gap-1 rounded-lg px-1 py-1">
              {["product", "resources", "company", "socials"].map((menu) => (
                <button
                  key={menu}
                  className="relative flex h-9 cursor-pointer items-center rounded-xl! px-4 py-2 text-sm text-zinc-400 capitalize transition-colors hover:text-zinc-100"
                  onMouseEnter={() => handleMouseEnter(menu)}
                >
                  {hoveredItem === menu && (
                    <motion.div
                      layoutId="navbar-pill"
                      className="absolute inset-0 h-full w-full rounded-lg bg-zinc-800 font-medium!"
                      initial={false}
                      transition={{
                        type: "spring",
                        stiffness: 300,
                        damping: 30,
                      }}
                    />
                  )}
                  <div className="relative z-10 flex items-center gap-2">
                    <span>{menu.charAt(0).toUpperCase() + menu.slice(1)}</span>
                    <ChevronDown height={17} width={17} />
                  </div>
                </button>
              ))}
            </div>
          )}

          {isMobileScreen ? (
            <div className="hidden" />
          ) : (
            <div className="hidden items-center gap-3 sm:flex">
              <RainbowGithubButton />
              <LinkButton
                size="sm"
                className="h-9 max-h-9 min-h-9 rounded-xl bg-primary px-4! text-sm font-medium text-black transition-all! hover:scale-105 hover:bg-primary!"
                as={Link}
                href={user.email ? "/c" : "/signup"}
              >
                {user.email && (
                  <BubbleConversationChatIcon
                    className="w-[15px] min-w-[15px]"
                    color="#000000"
                    width="19"
                  />
                )}
                {user.email ? "Chat" : "Get Started"}
              </LinkButton>
            </div>
          )}
        </div>

        {activeDropdown && (
          <NavbarMenu
            activeMenu={activeDropdown}
            onClose={() => setActiveDropdown(null)}
          />
        )}
      </div>
    </div>
  );
}
