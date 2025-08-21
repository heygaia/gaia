import { apiService } from "@/lib/api";

import { Integration, IntegrationStatus } from "../types";

export interface IntegrationStatusResponse {
  integrations: IntegrationStatus[];
}

export interface IntegrationConfigResponse {
  integrations: Integration[];
}

export const integrationsApi = {
  /**
   * Get the configuration for all integrations from backend
   */
  getIntegrationConfig: async (): Promise<IntegrationConfigResponse> => {
    try {
      const response = (await apiService.get(
        "/oauth/integrations/config",
      )) as IntegrationConfigResponse;
      return response;
    } catch (error) {
      console.error("Failed to get integration config:", error);
      throw error;
    }
  },
  /**
   * Get the status of all integrations for the current user
   */
  getIntegrationStatus: async (): Promise<IntegrationStatusResponse> => {
    try {
      const response = (await apiService.get("/oauth/integrations/status", {
        silent: true,
      })) as {
        integrations: Array<{
          integrationId: string;
          connected: boolean;
        }>;
        debug?: {
          authorized_scopes: string[];
        };
      };

      // Map backend response to frontend format
      const integrations: IntegrationStatus[] = response.integrations.map(
        (integration) => ({
          integrationId: integration.integrationId,
          connected: integration.connected,
          lastConnected: integration.connected
            ? new Date().toISOString()
            : undefined,
        }),
      );

      return { integrations };
    } catch (error) {
      console.error("Failed to get integration status:", error);
      // Return empty array if we can't determine status
      return {
        integrations: [],
      };
    }
  },

  /**
   * Initiate OAuth flow for an integration
   */
  connectIntegration: async (integrationId: string): Promise<void> => {
    // Get the integration config first
    const configResponse = await integrationsApi.getIntegrationConfig();
    const integration = configResponse.integrations.find(
      (i) => i.id === integrationId,
    );

    if (!integration || !integration.loginEndpoint) {
      throw new Error(
        `Integration ${integrationId} is not available for connection`,
      );
    }

    // Use the backend API base URL for proper OAuth flow
    const backendUrl = process.env.NEXT_PUBLIC_API_BASE_URL;
    const fullUrl = `${backendUrl}${integration.loginEndpoint}`;

    // Navigate to OAuth endpoint
    window.location.href = fullUrl;
  },

  /**
   * Disconnect an integration (placeholder for future implementation)
   */
  disconnectIntegration: async (integrationId: string): Promise<void> => {
    // This would call a disconnect endpoint in the future
    throw new Error(
      `Disconnect functionality not implemented yet for ${integrationId}`,
    );
  },
};
