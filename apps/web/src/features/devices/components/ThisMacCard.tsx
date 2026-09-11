"use client";

import { Button } from "@heroui/button";
import { Chip } from "@heroui/chip";
import { Spinner } from "@heroui/spinner";
import { Switch } from "@heroui/switch";
import { ComputerIcon, Delete02Icon, Folder01Icon, Link04Icon } from "@icons";
import type { ServerConfig } from "@shared/bridge-core/config.types";
import type { UseBridge } from "../hooks/useBridge";
import { thisDeviceLabel } from "../hooks/useDesktopPlatform";
import { AddServerModal } from "./AddServerModal";
import { FileAccessSection } from "./FileAccessSection";

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
      {server.type === "filesystem" ? (
        <Folder01Icon className="size-4 text-zinc-400" />
      ) : (
        <Link04Icon className="size-4 text-zinc-400" />
      )}
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

/**
 * "This computer" — the desktop app's own device, controlled in-app over the
 * bridge IPC surface (no CLI, no pairing code). Renders only inside the desktop
 * app (gated by the caller). Pairing is one click and the tunnel toggles live;
 * while connected GAIA can run commands and read/write files on the machine
 * (via run_on_device). On macOS the file-access section grants the OS-level
 * permissions those commands need (per-folder prompts + Full Disk Access).
 */
export function ThisMacCard({
  bridge,
  platform,
}: {
  bridge: UseBridge;
  platform: NodeJS.Platform | null;
}) {
  const { status, servers, busy, pair, setRunning, addServer, removeServer } =
    bridge;
  const label = thisDeviceLabel(platform);
  const noun = platform === "darwin" ? "this Mac" : "this computer";

  return (
    <div className="rounded-2xl bg-zinc-800 p-4">
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-start gap-3">
          <ComputerIcon className="mt-0.5 size-5 text-zinc-400" />
          <div>
            <div className="flex items-center gap-2">
              <span className="font-medium">{label}</span>
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
              aria-label={`Keep ${noun} connected`}
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
            Enable on {noun}
          </Button>
        )}
      </div>

      {status.paired && (
        <div className="mt-3 flex flex-col gap-2">
          {servers.map((server) => (
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
          {platform === "darwin" && <FileAccessSection />}
        </div>
      )}
    </div>
  );
}
