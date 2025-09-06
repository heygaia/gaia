import Image from "next/image";
import React from "react";

import { ArrowRight01Icon, Button } from "@/components";

interface Integration {
  id: string;
  name: string;
  icons: string[];
}

interface IntegrationsBannerProps {
  integrations: Integration[];
  isLoading: boolean;
  hasMessages: boolean;
  onToggleSlashCommand: () => void;
}

const IntegrationsBanner: React.FC<IntegrationsBannerProps> = ({
  integrations,
  isLoading,
  hasMessages,
  onToggleSlashCommand,
}) => {
  // Don't render if loading, no integrations, or if there are already messages
  if (isLoading || integrations.length === 0 || hasMessages) {
    return null;
  }

  return (
    <Button
      className="absolute -top-4 z-[0] flex h-fit w-[92%] rounded-full bg-zinc-800/40 px-4 py-2 pb-8 text-xs text-foreground-300 hover:bg-zinc-800/70 hover:text-zinc-400 sm:w-[46%]"
      onClick={onToggleSlashCommand}
    >
      <div className="flex w-full items-center justify-between">
        <span className="text-xs">Connect your tools to GAIA</span>
        <div className="ml-3 flex items-center gap-1">
          {integrations.slice(0, 8).map((integration) => (
            <div
              key={integration.id}
              className="opacity-60 transition duration-200 hover:scale-150 hover:rotate-6 hover:opacity-120"
              title={integration.name}
            >
              <Image
                width={14}
                height={14}
                src={integration.icons[0]}
                alt={integration.name}
                className="h-[14px] w-[14px] object-contain"
              />
            </div>
          ))}
          <ArrowRight01Icon width={18} height={18} className="ml-3" />
        </div>
      </div>
    </Button>
  );
};

export default IntegrationsBanner;
