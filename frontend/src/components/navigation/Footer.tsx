import { ArrowUpRight } from "lucide-react";
import Image from "next/image";

import { LinkButton } from "@/components/shared/LinkButton";
import { appConfig, footerSections } from "@/config/appConfig";
import { useUser } from "@/features/auth/hooks/useUser";

export default function Footer() {
  const user = useUser();
  const isAuthenticated = user?.email;

  return (
    <div className="relative z-[1] m-0! border-t-1 border-t-zinc-800 bg-gradient-to-t from-black to-zinc-950">
      <div className="flex h-fit w-screen items-center justify-center p-5 sm:p-20 sm:pb-5">
        <div className="grid w-full max-w-(--breakpoint-lg) grid-cols-2 gap-8 sm:grid-cols-5">
          <div className="flex h-full w-fit flex-col gap-1 text-foreground-600">
            <Image
              src="/branding/logo.webp"
              alt="GAIA Logo"
              width={40}
              height={40}
            />
            <div className="mt-2 text-2xl font-medium text-white">
              {appConfig.site.name}
            </div>
            <div className="flex flex-col gap-2 text-xs text-foreground-400">
              <div>{appConfig.site.copyright}</div>
            </div>
          </div>

          {footerSections.map((section) => (
            <div
              key={section.title}
              className="flex h-full w-fit flex-col text-foreground-500"
            >
              <div className="mb-3 pl-2 text-sm text-foreground">
                {section.title}
              </div>
              {section.links
                .filter(
                  (link) =>
                    (!link.requiresAuth && !link.guestOnly) ||
                    (link.requiresAuth && isAuthenticated) ||
                    (link.guestOnly && !isAuthenticated),
                )
                .map((link) => (
                  <div key={link.href}>
                    <LinkButton
                      href={link.href}
                      className="group relative flex items-center justify-start text-white"
                    >
                      {section.title == "Connect" &&
                        link.label !== "Contact Us" &&
                        link.icon && (
                          <div className="text-foreground-400 group-hover:text-foreground">
                            {link.icon}
                          </div>
                        )}
                      <span className="text-foreground-400 transition-colors group-hover:text-foreground">
                        {link.label}
                      </span>
                      <span className="ml-1 -translate-x-10 opacity-0 transition-all duration-150 group-hover:translate-x-0 group-hover:opacity-100">
                        <ArrowUpRight width={17} />
                      </span>
                    </LinkButton>
                  </div>
                ))}
            </div>
          ))}
        </div>
      </div>
      <div className="flex w-full items-center justify-center py-10">
        <iframe
          src="https://status.heygaia.io/badge?theme=dark"
          width="200"
          height="40"
          scrolling="no"
          style={{ colorScheme: "normal" }}
        />
      </div>
    </div>
  );
}
