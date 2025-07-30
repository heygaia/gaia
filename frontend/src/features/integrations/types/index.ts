/**
 * Integration system types and interfaces
 */

export interface Integration {
  id: string;
  name: string;
  description: string;
  icon: string;
  category:
    | "productivity"
    | "communication"
    | "storage"
    | "development"
    | "creative";
  status: "connected" | "not_connected" | "error";
  loginEndpoint?: string;
  disconnectEndpoint?: string;
  settingsPath?: string;
}

export interface IntegrationStatus {
  integrationId: string;
  connected: boolean;
  lastConnected?: string;
  error?: string;
  metadata?: Record<string, unknown>;
}

export interface IntegrationCategory {
  id: string;
  name: string;
  description: string;
  icon: string;
  integrations: Integration[];
}

export type IntegrationAction =
  | "connect"
  | "disconnect"
  | "settings"
  | "refresh";

export interface IntegrationActionEvent {
  integration: Integration;
  action: IntegrationAction;
}
