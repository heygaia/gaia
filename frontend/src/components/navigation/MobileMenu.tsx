"use client";

import { Button } from "@heroui/button";
import * as VisuallyHidden from "@radix-ui/react-visually-hidden";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { Menu01Icon } from "@/components/shared/icons";
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from "@/components/ui/shadcn/sheet";
import {
  auth,
  company,
  connect,
  main,
  product,
  resources,
} from "@/config/appConfig";
import { useUser } from "@/features/auth/hooks/useUser";

export default function MobileMenu() {
  const [sheetOpen, setSheetOpen] = useState(false);
  const user = useUser();
  const isAuthenticated = user?.email; // Check if user has email to determine auth status
  const router = useRouter();

  return (
    <Sheet open={sheetOpen} onOpenChange={setSheetOpen}>
      <SheetTrigger>
        <div className="rounded-full p-3">
          <Menu01Icon color="foreground" />
        </div>
      </SheetTrigger>
      <SheetContent className="max-w-[250px] border-none bg-zinc-900 text-foreground dark">
        <SheetHeader>
          <SheetTitle>
            <VisuallyHidden.Root>Menu</VisuallyHidden.Root>
          </SheetTitle>
          <SheetDescription className="flex flex-col gap-3 pt-12">
            {/* Main navigation links */}
            {main.map((link) => (
              <Button
                key={link.href}
                className="flex w-full justify-between"
                endContent={link.icon}
                color="default"
                as={link.external ? Link : undefined}
                href={link.external ? link.href : undefined}
                onPress={() => {
                  if (!link.external) {
                    router.push(link.href);
                    setSheetOpen(false);
                  }
                }}
              >
                {link.label}
              </Button>
            ))}

            {/* Product Section */}
            <div className="mt-4 border-t border-zinc-700 pt-4">
              <p className="mb-2 text-xs font-semibold tracking-wide text-zinc-400 uppercase">
                Product
              </p>
              {product.map((link) => {
                const isCommented = link.commented;
                return (
                  <Button
                    key={link.href}
                    className={`flex w-full justify-between ${isCommented ? "cursor-not-allowed opacity-50" : ""}`}
                    endContent={link.icon}
                    color="default"
                    variant="ghost"
                    disabled={isCommented}
                    as={!isCommented && link.external ? Link : undefined}
                    href={!isCommented && link.external ? link.href : undefined}
                    onPress={() => {
                      if (!isCommented && !link.external) {
                        router.push(link.href);
                        setSheetOpen(false);
                      }
                    }}
                  >
                    {isCommented ? `${link.label} (Coming Soon)` : link.label}
                  </Button>
                );
              })}
            </div>

            {/* Resources Section */}
            <div className="mt-4 border-t border-zinc-700 pt-4">
              <p className="mb-2 text-xs font-semibold tracking-wide text-zinc-400 uppercase">
                Resources
              </p>
              {resources.map((link) => {
                const isCommented = link.commented;
                return (
                  <Button
                    key={link.href}
                    className={`flex w-full justify-between ${isCommented ? "cursor-not-allowed opacity-50" : ""}`}
                    endContent={link.icon}
                    color="default"
                    variant="ghost"
                    disabled={isCommented}
                    as={!isCommented && link.external ? Link : undefined}
                    href={!isCommented && link.external ? link.href : undefined}
                    onPress={() => {
                      if (!isCommented && !link.external) {
                        router.push(link.href);
                        setSheetOpen(false);
                      }
                    }}
                  >
                    {isCommented ? `${link.label} (Coming Soon)` : link.label}
                  </Button>
                );
              })}
            </div>

            {/* Company Section */}
            <div className="mt-4 border-t border-zinc-700 pt-4">
              <p className="mb-2 text-xs font-semibold tracking-wide text-zinc-400 uppercase">
                Company
              </p>
              {company.map((link) => (
                <Button
                  key={link.href}
                  className="flex w-full justify-between"
                  endContent={link.icon}
                  color="default"
                  variant="ghost"
                  as={link.external ? Link : undefined}
                  href={link.external ? link.href : undefined}
                  onPress={() => {
                    if (!link.external) {
                      router.push(link.href);
                      setSheetOpen(false);
                    }
                  }}
                >
                  {link.label}
                </Button>
              ))}
            </div>

            {/* Connect Section */}
            <div className="mt-4 border-t border-zinc-700 pt-4">
              <p className="mb-2 text-xs font-semibold tracking-wide text-zinc-400 uppercase">
                Connect
              </p>
              {connect.map((link) => (
                <Button
                  key={link.href}
                  className="flex w-full justify-between"
                  endContent={link.icon}
                  color="default"
                  variant="ghost"
                  as={Link}
                  href={link.href}
                  target={link.external ? "_blank" : undefined}
                  rel={link.external ? "noopener noreferrer" : undefined}
                >
                  {link.label}
                </Button>
              ))}
            </div>

            {/* Authentication related links */}
            {isAuthenticated ? (
              // Show auth links that require login
              auth
                .filter((link) => link.requiresAuth)
                .map((link) => (
                  <Button
                    key={link.href}
                    className="font-medium"
                    color="primary"
                    endContent={link.icon}
                    size="md"
                    variant="shadow"
                    onPress={() => {
                      router.push(link.href);
                      setSheetOpen(false);
                    }}
                  >
                    {link.label}
                  </Button>
                ))
            ) : (
              // Show auth links for guests only
              <>
                {auth
                  .filter((link) => link.guestOnly)
                  .map((link) => (
                    <Button
                      key={link.href}
                      as={Link}
                      className="p-0 px-4 font-semibold"
                      color="primary"
                      size="md"
                      variant="shadow"
                      href={link.href}
                    >
                      {link.label}
                    </Button>
                  ))}
              </>
            )}
          </SheetDescription>
        </SheetHeader>
      </SheetContent>
    </Sheet>
  );
}
