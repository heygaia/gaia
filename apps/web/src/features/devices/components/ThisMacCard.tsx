"use client";

import { Button } from "@heroui/button";
import { Chip } from "@heroui/chip";
import { Spinner } from "@heroui/spinner";
import { Switch } from "@heroui/switch";
import { ComputerIcon, Delete02Icon, Folder01Icon, Link04Icon } from "@icons";
import type { ServerConfig } from "@shared/bridge-core/config.types";
import { ENTIRE_FS_PATH } from "../constants";
import type { UseBridge } from "../hooks/useBridge";
import { AddServerModal } from "./AddServerModal";

function StatusChip({
  paired,
  running,
}: {
  paired: boolean;
  running: boolean;
}) {
  if (!paired)
    return (
      <Chip size="sm" variant="flat" color="default">
        Not connected
      </Chip>
    );
  return (
    <Chip size="sm" variant="flat" color={running ? "success" : "warning"}>
      {running ? "Online" : "Paused"}
    </Chip>
  );
}

function ServerRow({
  server,
  onRemove,
  disabled,
}: {
  server: ServerConfig;
  onRemove: (key: string) => void;
  disabled: boolean;
}) {
  return (
    <div className="flex items-center gap-2 rounded-2xl bg-zinc-900 p-3 text-sm">
      <Link04Icon className="size-4 text-zinc-400" />
      <span className="min-w-0 flex-1 truncate">{server.name}</span>
      <Button
        isIconOnly
        size="sm"
        variant="light"
        color="danger"
        isDisabled={disabled}
        aria-label={`Remove ${server.name}`}
        onPress={() => onRemove(server.key)}
      >
        <Delete02Icon className="size-4" />
      </Button>
    </div>
  );
}

/** One switch for whole-machine file access — GAIA gets the entire filesystem
 * (read + write), like a local coding agent, instead of the user curating
 * folders. macOS still gates protected folders behind Full Disk Access. */
function FileAccessRow({
  enabled,
  disabled,
  onToggle,
}: {
  enabled: boolean;
  disabled: boolean;
  onToggle: (on: boolean) => void;
}) {
  return (
    <div className="flex items-center justify-between gap-3 rounded-2xl bg-zinc-900 p-3">
      <div className="flex items-start gap-2">
        <Folder01Icon className="mt-0.5 size-4 text-zinc-400" />
        <div>
          <p className="text-sm text-zinc-100">Full file access</p>
          <p className="text-xs text-zinc-500">
            Let GAIA read and edit files anywhere on this Mac. Protected folders
            (Downloads, Desktop, Documents) also need Full Disk Access granted
            to GAIA in System Settings.
          </p>
        </div>
      </div>
      <Switch
        size="sm"
        isSelected={enabled}
        isDisabled={disabled}
        onValueChange={onToggle}
        aria-label="Full file access"
      />
    </div>
  );
}

/**
 * "This Mac" — the desktop app's own device, controlled in-app over the bridge
 * IPC surface (no CLI, no pairing code). Renders only inside the desktop app
 * (gated by the caller); pairing is one click, the tunnel toggles live, file
 * access is a single switch, and MCP servers are added/removed here.
 */
export function ThisMacCard({ bridge }: { bridge: UseBridge }) {
  const { status, servers, busy, pair, setRunning, addServer, removeServer } =
    bridge;

  // Whole-machine file access is the built-in filesystem server; the rest of the
  // list is the user's own stdio/url MCP servers.
  const fileServer = servers.find((server) => server.type === "filesystem");
  const mcpServers = servers.filter((server) => server.type !== "filesystem");

  const toggleFileAccess = (on: boolean) => {
    if (on) {
      void addServer({
        type: "filesystem",
        path: [ENTIRE_FS_PATH],
        write: true,
      });
    } else if (fileServer) {
      void removeServer(fileServer.key);
    }
  };

  return (
    <div className="rounded-2xl bg-zinc-800 p-4">
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-start gap-3">
          <ComputerIcon className="mt-0.5 size-5 text-zinc-400" />
          <div>
            <div className="flex items-center gap-2">
              <span className="font-medium">This Mac</span>
              <StatusChip paired={status.paired} running={status.running} />
            </div>
            <p className="text-sm text-zinc-500">
              Runs inside the GAIA desktop app — no CLI needed.
            </p>
          </div>
        </div>
        {status.paired ? (
          <div className="flex items-center gap-2">
            {busy === "toggle" && <Spinner size="sm" />}
            <Switch
              size="sm"
              isSelected={status.running}
              isDisabled={busy === "toggle"}
              onValueChange={(next) => void setRunning(next)}
              aria-label="Keep this Mac connected"
            />
          </div>
        ) : (
          <Button
            size="sm"
            color="primary"
            variant="flat"
            isLoading={busy === "pair"}
            onPress={() => void pair()}
          >
            Enable on this Mac
          </Button>
        )}
      </div>

      {status.paired && (
        <div className="mt-3 flex flex-col gap-2">
          <FileAccessRow
            enabled={fileServer !== undefined}
            disabled={busy === "server"}
            onToggle={toggleFileAccess}
          />
          {mcpServers.map((server) => (
            <ServerRow
              key={server.key}
              server={server}
              onRemove={(key) => void removeServer(key)}
              disabled={busy === "server"}
            />
          ))}
          <div className="flex">
            <AddServerModal onAdd={addServer} isBusy={busy === "server"} />
          </div>
        </div>
      )}
    </div>
  );
}
