import { Button } from "@heroui/button";
import { Chip } from "@heroui/chip";
import { AlertCircleIcon } from "@icons";
import { CONNECT_ACTION_LABEL, connectionPromptState } from "@shared/utils";
import CollapsibleListWrapper from "@/components/shared/CollapsibleListWrapper";
import { getToolCategoryIcon } from "@/features/chat/utils/toolIcons";
import { BearerTokenModal } from "@/features/integrations/components/BearerTokenModal";
import { useBearerTokenModal } from "@/features/integrations/hooks/useBearerTokenModal";
import { useIntegrations } from "@/features/integrations/hooks/useIntegrations";
import type { IntegrationConnectionData } from "@/features/integrations/types";

interface IntegrationConnectionPromptProps {
  integration_connection_required: IntegrationConnectionData;
}

export default function IntegrationConnectionPrompt({
  integration_connection_required,
}: IntegrationConnectionPromptProps) {
  const { integration_id, message, expired } = integration_connection_required;
  const { integrations, connectIntegration } = useIntegrations();
  const bearer = useBearerTokenModal({
    connect: (id, token) => connectIntegration(id, token),
    onConnected: () => {
      // connectIntegration already toasts success and invalidates the
      // integration/tool caches, so there is nothing extra to do here.
    },
  });

  const integration = integrations.find((i) => i.id === integration_id);

  if (!integration) {
    return null;
  }

  const state = connectionPromptState(expired, integration.status);
  const isConnected = state === "connected";
  const isAvailable = integration.source === "custom" || integration.available;
  // API-key (bearer) servers collect their token in a secure modal — never in
  // chat and never through the LLM. Everything else uses OAuth/direct connect.
  const needsBearerToken =
    integration.authType === "bearer" && integration.requiresAuth;

  const handleConnect = async () => {
    if (needsBearerToken) {
      bearer.open(integration.id, integration.name);
      return;
    }
    try {
      await connectIntegration(integration.id);
    } catch (error) {
      console.error("Failed to connect integration:", error);
    }
  };

  const content = (
    <div className="w-fit max-w-2xl rounded-3xl bg-zinc-800/50 p-4 text-white">
      <div className="flex flex-col gap-3">
        <div className="flex items-start gap-3">
          <div className="shrink-0 pt-0.5">
            {getToolCategoryIcon(integration_id, {
              size: 22,
              width: 22,
              height: 22,
              showBackground: false,
            })}
          </div>

          <div className="flex min-w-0 flex-1 flex-col gap-1">
            <div className="flex items-center gap-2">
              <span className="text-sm font-medium">{integration.name}</span>
              {isConnected ? (
                <Chip size="sm" variant="flat" color="success">
                  Connected
                </Chip>
              ) : (
                <Chip
                  size="sm"
                  variant="flat"
                  color={state === "expired" ? "danger" : "warning"}
                >
                  {state === "expired" ? "Disconnected" : "Not Connected"}
                </Chip>
              )}
            </div>

            <p className="text-xs font-light text-zinc-400">
              {integration.description}
            </p>
          </div>
        </div>

        {!isConnected && isAvailable && (
          <div className="flex gap-2 w-full">
            {!isConnected && (
              <div className="flex w-fit gap-2 rounded-xl items-center bg-warning-100/10 p-3">
                <AlertCircleIcon
                  className="mt-0.5 shrink-0 text-warning-500"
                  size={16}
                />
                {/* The card grows to fit this line rather than wrapping it. */}
                <p className="whitespace-nowrap text-xs text-warning-700 dark:text-warning-400">
                  {message}
                </p>
              </div>
            )}

            {isAvailable && !isConnected && (
              <Button
                color={state === "expired" ? "warning" : "primary"}
                onPress={handleConnect}
              >
                {CONNECT_ACTION_LABEL[state]}
              </Button>
            )}
          </div>
        )}
      </div>
    </div>
  );

  return (
    <>
      <CollapsibleListWrapper
        icon={getToolCategoryIcon(integration_id, {
          size: 20,
          width: 20,
          height: 20,
          showBackground: false,
        })}
        count={1}
        label={
          state === "expired" ? "Reconnect Required" : "Integration Required"
        }
        isCollapsible={true}
      >
        {content}
      </CollapsibleListWrapper>
      <BearerTokenModal
        isOpen={bearer.isOpen}
        onClose={bearer.close}
        integrationId={bearer.integrationId}
        integrationName={bearer.integrationName}
        onSubmit={bearer.submit}
      />
    </>
  );
}
