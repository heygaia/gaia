"use client";

import { AiBrain01Icon } from "@/components/shared/icons";
import MemoryManagement from "@/features/memory/components/MemoryManagement";
import { SettingsCard } from "@/features/settings/components/SettingsCard";

export default function MemorySettings() {
  return (
    <div className="h-full w-full space-y-6">
      {/* Memory Management */}
      <SettingsCard
        icon={<AiBrain01Icon className="h-5 w-5" />}
        title="Memory Management"
        className="flex h-full flex-col"
      >
        <p className="mb-6 text-sm text-zinc-400">
          Manage the information GAIA remembers from your conversations
        </p>
        <MemoryManagement />
      </SettingsCard>
    </div>
  );
}
