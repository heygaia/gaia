"use client";

import { Button } from "@heroui/button";
import { Chip } from "@heroui/chip";
import { ArrowUpRight01Icon, ComputerIcon } from "@icons";
import NextLink from "next/link";
import type { DeviceApprovalRequiredData } from "@/features/devices/types";

interface DeviceApprovalPromptProps {
  device_approval_required: DeviceApprovalRequiredData;
}

export function DeviceApprovalPrompt({
  device_approval_required,
}: DeviceApprovalPromptProps) {
  const { approve_url, code, message } = device_approval_required;

  return (
    <div className="w-fit max-w-md rounded-2xl bg-zinc-800 p-4 text-white">
      <div className="flex flex-col gap-3">
        <div className="flex items-start gap-3">
          <div className="shrink-0 pt-0.5">
            <ComputerIcon width={22} height={22} className="text-primary" />
          </div>
          <div className="flex min-w-0 flex-1 flex-col gap-1">
            <span className="text-sm font-medium">Approve this device</span>
            <p className="text-xs font-light text-zinc-400">{message}</p>
          </div>
        </div>

        <div className="flex items-center justify-between gap-3 rounded-2xl bg-zinc-900 p-3">
          <Chip variant="flat" color="primary" className="font-mono">
            {code}
          </Chip>
          <Button
            as={NextLink}
            href={approve_url}
            color="primary"
            size="sm"
            endContent={<ArrowUpRight01Icon width={16} height={16} />}
          >
            Review &amp; approve
          </Button>
        </div>
      </div>
    </div>
  );
}
