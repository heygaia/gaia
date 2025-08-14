/**
 * Integration system types and interfaces
 */

export interface Integration {
  id: string;
  name: string;
  description: string;
  icons: string[]; // List of icon URLs
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
  // New properties for unified integrations
  isSpecial?: boolean;
  displayPriority?: number;
  includedIntegrations?: string[];
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
  icons: string[]; // List of icon URLs
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
