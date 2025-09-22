"use client";

import Image from "next/image";
import Link from "next/link";
import React from "react";

import {
  company,
  connect,
  getLinkDescription,
  product,
  resources,
} from "@/config/appConfig";
import { cn } from "@/lib/utils";

interface NavbarMenuProps {
  activeMenu: string;
  onClose: () => void;
}

const ListItem = React.forwardRef<
  React.ComponentRef<"a">,
  React.ComponentPropsWithoutRef<"a"> & {
    title: string;
    children?: React.ReactNode;
    href: string;
    external?: boolean;
    icon?: React.ReactNode;
  }
>(({ className, title, children, href, external, icon, ...props }, ref) => {
  const Component = external ? "a" : Link;
  const linkProps = external
    ? { href, target: "_blank", rel: "noopener noreferrer" }
    : { href };

  return (
    <li className="list-none">
      <Component
        ref={ref}
        className={cn(
          "flex h-full min-h-20 w-full flex-col justify-start rounded-xl bg-[#101112] p-4 leading-none no-underline transition-all duration-150 select-none hover:bg-[#191a1b] hover:text-zinc-100 focus:bg-zinc-800 focus:text-zinc-100",
          className,
        )}
        {...linkProps}
        {...props}
      >
        <div className="flex items-center gap-2">
          {icon && (
            <span className="flex-shrink-0 text-primary group-hover:text-zinc-300">
              {icon}
            </span>
          )}
          <div className="text-base leading-none font-medium text-zinc-100">
            {title}
          </div>
        </div>
        {children && (
          <p className="mt-1 line-clamp-2 text-sm leading-tight text-zinc-400">
            {children}
          </p>
        )}
      </Component>
    </li>
  );
});
ListItem.displayName = "ListItem";

export function NavbarMenu({ activeMenu, onClose }: NavbarMenuProps) {
  const getDescription = (label: string): string => {
    return getLinkDescription(label);
  };

  const getMenuLinks = () => {
    switch (activeMenu) {
      case "product":
        return product;
      case "resources":
        return resources;
      case "company":
        return company;
      case "socials":
        return connect;
      default:
        return [];
    }
  };

  const links = getMenuLinks();

  return (
    <div className="animate-in fade-in-0 slide-in-from-top-1 absolute top-full left-0 z-40 w-full rounded-b-2xl border-t-0 border-[#ffffff26] bg-[#08090A] shadow-2xl backdrop-blur-xl duration-200">
      <div className="p-6">
        {activeMenu === "product" && (
          <div className="grid w-full grid-cols-2 grid-rows-2 gap-4">
            <div className="row-span-2 md:col-span-1">
              <Link
                className="relative flex h-full w-full flex-col justify-end overflow-hidden rounded-2xl border border-zinc-800/50 bg-gradient-to-b from-zinc-900 to-zinc-950 p-3 no-underline transition-all duration-200 outline-none select-none hover:from-zinc-800 hover:to-zinc-900"
                href="/"
                onClick={onClose}
              >
                <Image
                  fill={true}
                  src="/images/logos/logo.webp"
                  alt="website logo"
                  className="relative z-0 scale-90 object-contain pb-10 opacity-5 grayscale-100"
                />
                <div className="relative z-[1] mt-4 text-lg font-medium text-zinc-100">
                  GAIA
                </div>
                <p className="relative z-[1] text-sm leading-tight text-zinc-400">
                  Your personal AI assistant
                </p>
              </Link>
            </div>
            {links.map((link) => (
              <ListItem
                key={link.href}
                href={link.href}
                title={link.label}
                external={link.external}
                icon={link.icon}
              >
                {getDescription(link.label)}
              </ListItem>
            ))}
          </div>
        )}

        {activeMenu === "resources" && (
          <div className="grid w-full grid-cols-2 grid-rows-2 gap-4">
            {links.map((link) => (
              <ListItem
                key={link.href}
                href={link.href}
                title={link.label}
                external={link.external}
                icon={link.icon}
              >
                {getDescription(link.label)}
              </ListItem>
            ))}
          </div>
        )}

        {activeMenu === "company" && (
          <div className="grid w-full grid-cols-2 grid-rows-2 gap-4">
            {links.map((link) => (
              <ListItem
                key={link.href}
                href={link.href}
                title={link.label}
                external={link.external}
                icon={link.icon}
              >
                {getDescription(link.label)}
              </ListItem>
            ))}
          </div>
        )}

        {activeMenu === "socials" && (
          <div className="grid w-full grid-cols-3 gap-4 md:grid-cols-3">
            {links.map((link) => (
              <ListItem
                key={link.href}
                href={link.href}
                title={link.label}
                external={link.external}
                icon={link.icon}
              >
                {getDescription(link.label)}
              </ListItem>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
