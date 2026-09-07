import { Button } from "@heroui/button";
import { Chip } from "@heroui/chip";
import { Input } from "@heroui/input";
import { Spinner } from "@heroui/spinner";
import { AlertCircleIcon } from "@icons";
import { CONNECT_ACTION_LABEL, connectionPromptState } from "@shared/utils";
import CollapsibleListWrapper from "@/components/shared/CollapsibleListWrapper";
import { getToolCategoryIcon } from "@/features/chat/utils/toolIcons";
import { useInlineIntegrationConnect } from "@/features/integrations/hooks/useInlineIntegrationConnect";
import { useIntegrations } from "@/features/integrations/hooks/useIntegrations";
import type {
  Integration,
  IntegrationConnectionData,
} from "@/features/integrations/types";

interface IntegrationConnectionPromptProps {
  integration_connection_required: IntegrationConnectionData;
}

function cardIcon(integrationId: string) {
  return getToolCategoryIcon(integrationId, {
    size: 22,
    width: 22,
    height: 22,
    showBackground: false,
  });
}

interface IntegrationConnectCardProps {
  integration: Integration;
  message: string;
  expired?: boolean;
}

// Owns the inline connect flow so the token stays local component state, cleared
// on success — never a chat message, a tool argument, or persisted anywhere.
function IntegrationConnectCard({
  integration,
  message,
  expired,
}: IntegrationConnectCardProps) {
  const { phase, token, setToken, toolsCount, error, connect } =
    useInlineIntegrationConnect(integration.id);

  const state = connectionPromptState(expired, integration.status);
  const isConnected = phase === "connected" || state === "connected";
  const isAvailable = integration.source === "custom" || integration.available;
  // Bearer/API-key servers collect their token in-card; the value is POSTed
  // straight to the API and never enters chat or the LLM.
  const needsBearerToken =
    integration.authType === "bearer" && integration.requiresAuth;
  const connecting = phase === "connecting";
  const failed = phase === "failed";

  return (
    <div className="w-fit max-w-2xl rounded-3xl bg-zinc-800/50 p-4 text-white">
      <div className="flex flex-col gap-3">
        <div className="flex items-start gap-3">
          <div className="shrink-0 pt-0.5">{cardIcon(integration.id)}</div>
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
                  color={failed || state === "expired" ? "danger" : "warning"}
                >
                  {failed
                    ? "Failed"
                    : state === "expired"
                      ? "Disconnected"
                      : "Not Connected"}
                </Chip>
              )}
            </div>
            <p className="text-xs font-light text-zinc-400">
              {isConnected && toolsCount != null
                ? `${toolsCount} tools available`
                : integration.description}
            </p>
          </div>
        </div>

        {!isConnected && isAvailable && (
          <div className="flex w-full flex-col gap-2">
            <div className="flex w-fit items-center gap-2 rounded-xl bg-warning-100/10 p-3">
              <AlertCircleIcon
                className="mt-0.5 shrink-0 text-warning-500"
                size={16}
              />
              <p className="text-xs text-warning-700 dark:text-warning-400">
                {failed ? error : message}
              </p>
            </div>

            <div className="flex items-center gap-2">
              {needsBearerToken && (
                <Input
                  type="password"
                  size="sm"
                  className="max-w-xs"
                  placeholder="Paste API token"
                  autoComplete="off"
                  value={token}
                  onValueChange={setToken}
                  isDisabled={connecting}
                />
              )}
              <Button
                color={failed || state === "expired" ? "warning" : "primary"}
                isLoading={connecting}
                isDisabled={needsBearerToken && !token.trim()}
                onPress={() => connect(needsBearerToken ? token : undefined)}
              >
                {failed ? "Retry" : CONNECT_ACTION_LABEL[state]}
              </Button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default function IntegrationConnectionPrompt({
  integration_connection_required,
}: IntegrationConnectionPromptProps) {
  const { integration_id, message, expired, integration_name } =
    integration_connection_required;
  const { integrations } = useIntegrations();
  const integration = integrations.find((i) => i.id === integration_id);

  return (
    <CollapsibleListWrapper
      icon={cardIcon(integration_id)}
      count={1}
      label={expired ? "Reconnect Required" : "Integration Required"}
      isCollapsible={true}
    >
      {integration ? (
        <IntegrationConnectCard
          integration={integration}
          message={message}
          expired={expired}
        />
      ) : (
        // Catalog still loading: header from the streamed name + spinner, rather
        // than flashing empty until /integrations/me resolves.
        <div className="flex w-fit items-center gap-3 rounded-3xl bg-zinc-800/50 p-4 text-white">
          <Spinner size="sm" />
          <span className="text-sm font-medium">
            {integration_name ?? "Integration"}
          </span>
        </div>
      )}
    </CollapsibleListWrapper>
  );
}
