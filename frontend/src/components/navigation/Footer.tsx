import { ArrowUpRight } from "lucide-react";
import Image from "next/image";

import { LinkButton } from "@/components/shared/LinkButton";
import { appConfig, footerSections, connect } from "@/config/appConfig";
import { useUser } from "@/features/auth/hooks/useUser";
import Link from "next/link";

export default function Footer() {
  const user = useUser();
  const isAuthenticated = user?.email;

  return (
    <div className="relative z-[1] m-0! flex flex-col items-center gap-7 overflow-hidden p-5 font-light sm:p-10 sm:pt-20 sm:pb-5">
      <div className="flex h-fit w-screen items-center justify-center">
        <div className="grid w-full max-w-5xl grid-cols-2 gap-8 sm:grid-cols-4">
          <div className="relative -top-2 flex h-full w-fit flex-col gap-1 text-foreground-600">
            <div className="flex w-fit items-center justify-center rounded-xl p-1">
              <iframe
                src="https://status.heygaia.io/badge?theme=dark"
                title="GAIA API Status"
                scrolling="no"
                height={30}
                width={186}
                style={{ colorScheme: "normal" }}
              />
            </div>

            <div className="mt-2 flex items-center gap-3 px-3 text-2xl font-medium text-white">
              <Link href={"/"}>
                <Image
                  src="/images/logos/logo.webp"
                  alt="GAIA Logo"
                  width={45}
                  height={45}
                />
              </Link>
            </div>
          </div>

          {footerSections.map((section) => (
            <div
              key={section.title}
              className="flex h-full w-full flex-col items-end text-foreground-500"
            >
              <div className="mb-3 pl-2 text-sm text-foreground">
                {section.title}
              </div>
              {section.links

                .filter(
                  (link) =>
                    ((!link.requiresAuth && !link.guestOnly) ||
                      (link.requiresAuth && isAuthenticated) ||
                      (link.guestOnly && !isAuthenticated)) &&
                    !link.hideFooter,
                )
                .sort((a, b) =>
                  a.label.localeCompare(b.label, undefined, {
                    sensitivity: "base",
                  }),
                )
                .map((link) => (
                  <Link
                    key={link.href}
                    href={link.href}
                    className="group relative flex w-full cursor-pointer justify-end py-1 text-sm"
                  >
                    {/* {section.title == "Connect" &&
                      link.label !== "Contact Us" &&
                      link.icon && (
                        <div className="group-hover:text-primary">
                          {link.icon}
                        </div>
                      )} */}
                    <span className="text-foreground-400 transition-colors group-hover:text-primary">
                      {link.label}
                    </span>
                    {/* <span className="ml-1 -translate-x-10 opacity-0 transition-all duration-150 group-hover:translate-x-0 group-hover:opacity-100">
                        <ArrowUpRight width={17} />
                      </span> */}
                  </Link>
                ))}
            </div>
          ))}
        </div>
      </div>
      <div className="mx-auto mt-10 flex w-full max-w-5xl items-center justify-between border-t-1 border-zinc-800 py-8 pb-3 text-xs font-light text-zinc-600">
        <div className="flex items-center gap-3">
          {connect.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              target={link.external ? "_blank" : "_self"}
              rel={link.external ? "noopener noreferrer" : undefined}
              className="cursor-pointer text-foreground-400 transition-colors hover:text-foreground"
              title={link.description}
            >
              {link.icon}
            </Link>
          ))}
        </div>
        <div>{appConfig.site.copyright}</div>

        <div className="flex border-separate items-center gap-2">
          <Link href={"/terms"} className="underline-offset-2 hover:underline">
            Terms of Use
          </Link>
          <div className="h-4 border-l border-zinc-800" />

          <Link
            href={"/privacy"}
            className="underline-offset-2 hover:underline"
          >
            Privacy Policy
          </Link>
        </div>
      </div>
    </div>
  );
}
