"use client";

import { Button } from "@heroui/button";
import { Input } from "@heroui/input";
import { Link } from "@heroui/link";
import { Snippet } from "@heroui/snippet";
import { BookOpen01Icon, CommandLineIcon, ComputerIcon } from "@icons";
import NextLink from "next/link";
import { type ReactNode, useState } from "react";
import CollapsibleListWrapper from "@/components/shared/CollapsibleListWrapper";
import type { DeviceOnboardingRequiredData } from "@/features/devices/types";

const APPROVE_PATH = "/settings/devices/approve";
const PACKAGE_MANAGERS = ["npm", "pnpm", "bun"] as const;
type PackageManager = (typeof PACKAGE_MANAGERS)[number];

interface DeviceOnboardingPromptProps {
  device_onboarding_required: DeviceOnboardingRequiredData;
}

function deviceIcon() {
  return <ComputerIcon width={22} height={22} className="text-zinc-300" />;
}

function StepCard({
  index,
  title,
  children,
}: {
  index: number;
  title: string;
  children: ReactNode;
}) {
  return (
    <div className="rounded-2xl bg-zinc-900 p-3">
      <div className="flex items-center gap-2">
        <span className="flex size-5 shrink-0 items-center justify-center rounded-full bg-zinc-800 text-[11px] font-medium text-zinc-400 tabular-nums">
          {index}
        </span>
        <p className="text-sm font-medium text-zinc-100">{title}</p>
      </div>
      <div className="mt-2 flex flex-col gap-2 pl-7">{children}</div>
    </div>
  );
}

function CommandSnippet({ command }: { command: string }) {
  return (
    <Snippet
      hideSymbol
      variant="flat"
      size="sm"
      codeString={command}
      className="w-full bg-zinc-800 text-zinc-200"
    >
      <span className="truncate font-mono text-xs">{command}</span>
    </Snippet>
  );
}

export function DeviceOnboardingPrompt({
  device_onboarding_required,
}: DeviceOnboardingPromptProps) {
  const { install_commands, docs_url, pair_command, up_command, message } =
    device_onboarding_required;
  const [packageManager, setPackageManager] = useState<PackageManager>("npm");
  const [code, setCode] = useState("");

  const trimmedCode = code.trim();
  const approveHref = trimmedCode
    ? `${APPROVE_PATH}?code=${encodeURIComponent(trimmedCode)}`
    : APPROVE_PATH;

  return (
    <CollapsibleListWrapper
      icon={deviceIcon()}
      count={1}
      label="Connect a device"
      isCollapsible={true}
    >
      <div className="w-fit max-w-2xl rounded-2xl bg-zinc-800 p-4 text-white">
        <div className="flex flex-col gap-3">
          <div className="flex items-start gap-3">
            <div className="shrink-0 pt-0.5">
              <CommandLineIcon
                width={22}
                height={22}
                className="text-primary"
              />
            </div>
            <div className="flex min-w-0 flex-1 flex-col gap-1">
              <span className="text-sm font-medium">Connect a device</span>
              <p className="text-xs font-light text-zinc-400">{message}</p>
            </div>
          </div>

          <StepCard index={1} title="Install the GAIA CLI">
            <div className="flex flex-wrap items-center gap-1.5">
              {PACKAGE_MANAGERS.map((pm) => (
                <Button
                  key={pm}
                  size="sm"
                  variant={pm === packageManager ? "solid" : "flat"}
                  color={pm === packageManager ? "primary" : "default"}
                  onPress={() => setPackageManager(pm)}
                >
                  {pm}
                </Button>
              ))}
            </div>
            <CommandSnippet command={install_commands[packageManager]} />
            <Link
              href={docs_url}
              isExternal
              showAnchorIcon
              size="sm"
              className="text-xs"
            >
              <BookOpen01Icon width={14} height={14} className="mr-1" />
              Setup guide
            </Link>
          </StepCard>

          <StepCard index={2} title="Pair this machine">
            <CommandSnippet command={pair_command} />
          </StepCard>

          <StepCard index={3} title="Enter the pairing code">
            <div className="flex flex-wrap items-center gap-2">
              <Input
                size="sm"
                className="max-w-[12rem]"
                placeholder="e.g. NS2V-YC5S"
                autoComplete="off"
                value={code}
                onValueChange={setCode}
                aria-label="Pairing code"
              />
              <Button
                as={NextLink}
                href={approveHref}
                color="primary"
                isDisabled={!trimmedCode}
              >
                Approve device
              </Button>
            </div>
            <p className="text-xs text-zinc-500">
              After approving, bring the device online with:
            </p>
            <CommandSnippet command={up_command} />
          </StepCard>
        </div>
      </div>
    </CollapsibleListWrapper>
  );
}
