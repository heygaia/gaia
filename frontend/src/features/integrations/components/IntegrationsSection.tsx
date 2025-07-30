import { Button } from "@heroui/button";
import { ScrollShadow } from "@heroui/scroll-shadow";
import { motion } from "framer-motion";
import { CheckCircle, ExternalLink, Plus, Settings } from "lucide-react";
import Image from "next/image";
import React from "react";

import { useIntegrations } from "../hooks/useIntegrations";
import { Integration } from "../types";

interface IntegrationsSectionProps {
  onClose?: () => void;
  maxHeight?: string;
}

const IntegrationCard: React.FC<{
  integration: Integration;
  onConnect: (id: string) => void;
  onDisconnect: (id: string) => void;
}> = ({ integration, onConnect, onDisconnect }) => {
  const isConnected = integration.status === "connected";
  const isAvailable = !!integration.loginEndpoint;

  return (
    <motion.div
      initial={{ opacity: 0, y: 4 }}
      animate={{ opacity: 1, y: 0 }}
      className="group relative mx-2 mb-2 cursor-pointer rounded-xl border border-transparent transition-all duration-150 hover:bg-white/5"
    >
      <div className="flex items-center gap-3 p-3">
        {/* Integration Icon */}
        <div className="flex-shrink-0">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-zinc-800/50">
            <Image
              src={integration.icon}
              alt={integration.name}
              width={20}
              height={20}
              className="h-5 w-5 object-contain"
              onError={(e) => {
                (e.target as HTMLImageElement).style.display = "none";
              }}
            />
          </div>
        </div>

        {/* Content */}
        <div className="min-w-0 flex-1">
          <div className="flex items-center justify-between gap-2">
            <div>
              <div className="flex items-center gap-2">
                <span className="text-sm font-medium text-white">
                  {integration.name}
                </span>
                {isConnected && (
                  <CheckCircle size={14} className="text-green-400" />
                )}
              </div>
              <p className="line-clamp-1 text-xs text-zinc-400">
                {integration.description}
              </p>
            </div>

            {/* Action Buttons */}
            <div className="flex items-center gap-1">
              {isConnected ? (
                <>
                  <Button
                    size="sm"
                    variant="flat"
                    isIconOnly
                    className="opacity-0 transition-opacity group-hover:opacity-100"
                    onPress={() => onDisconnect(integration.id)}
                  >
                    <Settings size={14} />
                  </Button>
                </>
              ) : isAvailable ? (
                <Button
                  size="sm"
                  variant="flat"
                  isIconOnly
                  className="opacity-0 transition-opacity group-hover:opacity-100"
                  onPress={() => onConnect(integration.id)}
                >
                  <Plus size={14} />
                </Button>
              ) : (
                <span className="rounded bg-zinc-800/50 px-2 py-1 text-xs text-zinc-500">
                  Soon
                </span>
              )}
            </div>
          </div>
        </div>
      </div>
    </motion.div>
  );
};

export const IntegrationsSection: React.FC<IntegrationsSectionProps> = ({
  onClose,
  maxHeight = "24rem",
}) => {
  const { integrations, connectIntegration, disconnectIntegration, isLoading } =
    useIntegrations();

  const handleConnect = async (integrationId: string) => {
    try {
      await connectIntegration(integrationId);
      onClose?.();
    } catch (error) {
      console.error("Failed to connect integration:", error);
    }
  };

  const handleDisconnect = async (integrationId: string) => {
    try {
      await disconnectIntegration(integrationId);
    } catch (error) {
      console.error("Failed to disconnect integration:", error);
    }
  };

  const connectedIntegrations = integrations.filter(
    (i) => i.status === "connected",
  );
  const availableIntegrations = integrations.filter(
    (i) => i.status === "not_connected" && i.loginEndpoint,
  );
  const comingSoonIntegrations = integrations.filter((i) => !i.loginEndpoint);

  if (isLoading) {
    return (
      <div className="px-4 py-6 text-center">
        <div className="text-sm text-zinc-400">Loading integrations...</div>
      </div>
    );
  }

  return (
    <ScrollShadow className="overflow-y-auto" style={{ maxHeight }}>
      <div className="py-2">
        {/* Connected Integrations */}
        {connectedIntegrations.length > 0 && (
          <div className="mb-4">
            <div className="mb-2 flex items-center gap-2 px-3">
              <CheckCircle size={16} className="text-green-400" />
              <span className="text-sm font-medium text-green-400">
                Connected
              </span>
            </div>
            {connectedIntegrations.map((integration) => (
              <IntegrationCard
                key={integration.id}
                integration={integration}
                onConnect={handleConnect}
                onDisconnect={handleDisconnect}
              />
            ))}
          </div>
        )}

        {/* Available Integrations */}
        {availableIntegrations.length > 0 && (
          <div className="mb-4">
            <div className="mb-2 flex items-center gap-2 px-3">
              <Plus size={16} className="text-blue-400" />
              <span className="text-sm font-medium text-blue-400">
                Available
              </span>
            </div>
            {availableIntegrations.map((integration) => (
              <IntegrationCard
                key={integration.id}
                integration={integration}
                onConnect={handleConnect}
                onDisconnect={handleDisconnect}
              />
            ))}
          </div>
        )}

        {/* Coming Soon */}
        {comingSoonIntegrations.length > 0 && (
          <div>
            <div className="mb-2 flex items-center gap-2 px-3">
              <ExternalLink size={16} className="text-zinc-500" />
              <span className="text-sm font-medium text-zinc-500">
                Coming Soon
              </span>
            </div>
            {comingSoonIntegrations.map((integration) => (
              <IntegrationCard
                key={integration.id}
                integration={integration}
                onConnect={handleConnect}
                onDisconnect={handleDisconnect}
              />
            ))}
          </div>
        )}

        {/* Empty State */}
        {integrations.length === 0 && (
          <div className="px-4 py-8 text-center">
            <div className="text-sm text-zinc-400">
              No integrations available
            </div>
          </div>
        )}
      </div>
    </ScrollShadow>
  );
};
