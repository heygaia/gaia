// The renderer-facing half of the device bridge: it registers one ipcMain.handle
// per bridge action, delegating each to the BridgeHost singleton, and pushes
// status changes to the main window so the UI (Phase 3) stays live.
//
// Every invoke resolves to a BridgeInvokeResult envelope rather than rejecting —
// a rejected handle() reaches the renderer as a wrapped stack string, so instead
// we catch and serialize the host's typed errors to { code, message } (R4: only
// status/error data crosses this boundary, never the device refresh token).

import type {
  BridgeError,
  BridgeInvokeResult,
  BridgeStatus,
  ServerConfig,
} from "@gaia/shared/bridge-core";
import { ipcMain } from "electron";
import { IPC } from "../../ipc-channels";
import { getMainWindow } from "../windows/main";
import {
  BridgeNotAuthenticatedError,
  BridgeNotPairedError,
  getBridgeHost,
} from "./host";

/** Map a thrown host error to the renderer contract. The typed pairing errors
 * get machine-readable codes; a server-message error (including the 409
 * device-cap) keeps its human-readable detail under `unknown`. */
function toBridgeError(error: unknown): BridgeError {
  if (error instanceof BridgeNotAuthenticatedError)
    return { code: "not_authenticated", message: error.message };
  if (error instanceof BridgeNotPairedError)
    return { code: "not_paired", message: error.message };
  return {
    code: "unknown",
    message: error instanceof Error ? error.message : String(error),
  };
}

/** Run a host operation and wrap its outcome in the invoke envelope, so the
 * handler never rejects and the renderer always gets a typed result. */
async function run<T>(
  op: () => T | Promise<T>,
): Promise<BridgeInvokeResult<T>> {
  try {
    return { ok: true, value: await op() };
  } catch (error) {
    const bridgeError = toBridgeError(error);
    console.error(
      `[bridge] ipc failure (${bridgeError.code}): ${bridgeError.message}`,
    );
    return { ok: false, error: bridgeError };
  }
}

/** Structural guard for an add-server payload arriving from the renderer. The
 * frame is untrusted over IPC, so validate the discriminant and its required
 * fields before handing it to the host rather than trusting the type. */
function isServerConfig(value: unknown): value is ServerConfig {
  if (typeof value !== "object" || value === null) return false;
  const cfg = value as Record<string, unknown>;
  if (typeof cfg["key"] !== "string" || cfg["key"].length === 0) return false;
  if (typeof cfg["name"] !== "string" || cfg["name"].length === 0) return false;
  switch (cfg["type"]) {
    case "filesystem":
      return (
        Array.isArray(cfg["allow"]) && typeof cfg["allowWrite"] === "boolean"
      );
    case "url":
      return typeof cfg["url"] === "string" && cfg["url"].length > 0;
    case "stdio":
      return (
        typeof cfg["command"] === "string" &&
        cfg["command"].length > 0 &&
        Array.isArray(cfg["args"]) &&
        typeof cfg["env"] === "object" &&
        cfg["env"] !== null
      );
    default:
      return false;
  }
}

function bridgePair(): Promise<BridgeInvokeResult<BridgeStatus>> {
  return run(async () => {
    const host = getBridgeHost();
    await host.pair();
    return host.status();
  });
}

function bridgeStatus(): Promise<BridgeInvokeResult<BridgeStatus>> {
  return run(() => getBridgeHost().status());
}

function bridgeStart(): Promise<BridgeInvokeResult<BridgeStatus>> {
  return run(async () => {
    const host = getBridgeHost();
    await host.start();
    return host.status();
  });
}

function bridgeStop(): Promise<BridgeInvokeResult<BridgeStatus>> {
  return run(async () => {
    const host = getBridgeHost();
    await host.stop();
    return host.status();
  });
}

function bridgeListServers(): Promise<BridgeInvokeResult<ServerConfig[]>> {
  return run(() => getBridgeHost().listServers());
}

function bridgeAddServer(
  config: unknown,
): Promise<BridgeInvokeResult<ServerConfig[]>> {
  return run(async () => {
    if (!isServerConfig(config)) throw new Error("invalid server config");
    const host = getBridgeHost();
    await host.addServer(config);
    return host.listServers();
  });
}

function bridgeRemoveServer(
  key: unknown,
): Promise<BridgeInvokeResult<ServerConfig[]>> {
  return run(async () => {
    if (typeof key !== "string" || key.length === 0)
      throw new Error("invalid server key");
    const host = getBridgeHost();
    await host.removeServer(key);
    return host.listServers();
  });
}

/** Forward a host status change to the main window's renderer. Guards a
 * destroyed/absent window (status can change before the window exists, or
 * after it closes on quit). */
function pushStatus(status: BridgeStatus): void {
  const win = getMainWindow();
  if (win && !win.isDestroyed()) {
    win.webContents.send(IPC.bridgeStatusChanged, status);
  }
}

/**
 * Register every bridge IPC handler and the status-change push. Called once
 * from {@link registerIpcHandlers}. Also configures the host's state dir up
 * front (cheap, no shell spawn) so status()/pair() resolve credentials
 * immediately without waiting on the PATH-resolving init() that only the
 * tunnel needs.
 */
export function registerBridgeIpcHandlers(): void {
  getBridgeHost().configureStateDir();

  ipcMain.handle(IPC.bridgePair, () => bridgePair());
  ipcMain.handle(IPC.bridgeStatus, () => bridgeStatus());
  ipcMain.handle(IPC.bridgeStart, () => bridgeStart());
  ipcMain.handle(IPC.bridgeStop, () => bridgeStop());
  ipcMain.handle(IPC.bridgeListServers, () => bridgeListServers());
  ipcMain.handle(IPC.bridgeAddServer, (_event, config: unknown) =>
    bridgeAddServer(config),
  );
  ipcMain.handle(IPC.bridgeRemoveServer, (_event, key: unknown) =>
    bridgeRemoveServer(key),
  );

  getBridgeHost().onStatusChange(pushStatus);
}
