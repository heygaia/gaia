export interface DeviceServer {
  server_key: string;
  display_name: string;
  integration_id: string;
  status: string;
  tools_synced_at: string | null;
}

export interface Device {
  id: string;
  name: string;
  platform: string | null;
  daemon_version: string | null;
  status: string;
  online: boolean;
  last_seen_at: string | null;
  created_at: string;
  servers: DeviceServer[];
}

export interface DeviceListResponse {
  devices: Device[];
}

export interface ApproveDeviceResponse {
  device_id: string;
  name: string;
}

/**
 * The `device_onboarding_required` chat payload — the agent asking the user to
 * install the bridge CLI and pair a machine before it can reach a local MCP
 * server. Purely instructional: the card renders these commands and links to the
 * authenticated approve page; it never runs or POSTs anything itself.
 *
 * `install_commands` is keyed by package manager (not OS): the same global
 * install expressed for npm / pnpm / bun, mirroring CLI_INSTALL_COMMANDS in
 * `@shared/cli/command-manifest`.
 */
export interface DeviceOnboardingRequiredData {
  install_commands: {
    npm: string;
    pnpm: string;
    bun: string;
  };
  docs_url: string;
  pair_command: string;
  up_command: string;
  message: string;
}

/**
 * The `device_approval_required` chat payload — a machine is waiting on a
 * pairing code. The card is presentational: it shows the code and routes the
 * user to the existing authenticated approve page (`approve_url`), which owns
 * the actual approval POST.
 */
export interface DeviceApprovalRequiredData {
  approve_url: string;
  code: string;
  message: string;
}
