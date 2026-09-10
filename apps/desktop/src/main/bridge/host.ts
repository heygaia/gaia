// Hosts the device bridge tunnel inside the Electron main process — the desktop
// equivalent of the CLI's `gaia bridge up` daemon. It configures bridge-core to
// keep state under userData/bridge and to spawn with the login-shell PATH, then
// supervises a single Tunnel: transient drops reconnect inside Tunnel.run(),
// while an auth exit (401/revoke) clears credentials and goes unpaired instead
// of hammering a dead token.
//
// Pairing (task 2.2) and IPC (task 2.3) are NOT wired here yet — this builds the
// host and its lifecycle only, exposed via the getBridgeHost() singleton getter.

import { EventEmitter } from "node:events";
import { join } from "node:path";
import {
  type BridgeLogger,
  clearCredentials,
  configureBridge,
  isPaired,
  loadConfig,
  loadCredentials,
  registerConfiguredServers,
  removeServer as removeServerFromConfig,
  type ServerConfig,
  Tunnel,
  upsertServer,
} from "@gaia/shared/bridge-core";
import { app } from "electron";
import { resolveLoginShellPath } from "./env";

/** Snapshot for the renderer/tray: whether this device is paired (has stored
 * credentials) and whether its tunnel is currently held open. */
export interface BridgeStatus {
  paired: boolean;
  running: boolean;
}

/** Thrown by start() when the device is not yet paired — pairing is task 2.2, so
 * until then start() has nothing to authenticate with. Typed so the IPC layer
 * (task 2.3) can surface "pair first" rather than a generic failure. */
export class BridgeNotPairedError extends Error {
  constructor() {
    super("bridge is not paired — pair this device before starting the tunnel");
    this.name = "BridgeNotPairedError";
  }
}

/** Consecutive unexpected-throw restarts before the supervisor gives up,
 * mirroring server.ts's Next.js supervisor. Transient network drops never reach
 * this — Tunnel.run() reconnects them internally with jittered backoff. */
const MAX_RESTART_ATTEMPTS = 3;
/** Delay between unexpected-throw restarts. */
const RESTART_DELAY_MS = 2_000;

const STATUS_EVENT = "status";

export class BridgeHost {
  private readonly events = new EventEmitter();
  private readonly logger: BridgeLogger = {
    info: (message) => console.log(message),
    error: (message) => console.error(message),
  };

  private tunnel: Tunnel | null = null;
  private initialized = false;
  private running = false;
  /** Set before we call tunnel.stop() so the supervise loop can tell a stop WE
   * asked for from an auth exit the tunnel decided on. */
  private intentionalStop = false;

  /** Configure bridge-core for this host: state under userData/bridge and a
   * login-shell PATH so spawned npx/uvx/node resolve from a Finder launch.
   * Idempotent — safe to call from every entry point. */
  async init(): Promise<void> {
    if (this.initialized) return;
    const loginPath = await resolveLoginShellPath();
    configureBridge({
      stateDir: join(app.getPath("userData"), "bridge"),
      env: { ...process.env, PATH: loginPath },
      shell: process.env["SHELL"] || "/bin/zsh",
      logger: this.logger,
    });
    this.initialized = true;
  }

  status(): BridgeStatus {
    return { paired: isPaired(), running: this.running };
  }

  onStatusChange(listener: (status: BridgeStatus) => void): void {
    this.events.on(STATUS_EVENT, listener);
  }

  offStatusChange(listener: (status: BridgeStatus) => void): void {
    this.events.off(STATUS_EVENT, listener);
  }

  /** Start the supervised tunnel. Throws BridgeNotPairedError if unpaired. The
   * tunnel is held in the background; this returns once it is running, not when
   * it stops. */
  async start(): Promise<void> {
    await this.init();
    if (!isPaired()) throw new BridgeNotPairedError();
    if (this.running) return;
    this.intentionalStop = false;
    this.running = true;
    this.emitStatus();
    void this.superviseLoop();
  }

  /** Stop the tunnel we are holding. Marks the stop as intentional so the
   * supervise loop does not mistake the resulting run() return for an auth
   * exit. */
  async stop(): Promise<void> {
    this.intentionalStop = true;
    const tunnel = this.tunnel;
    this.tunnel = null;
    if (tunnel) await tunnel.stop();
    if (this.running) {
      this.running = false;
      this.emitStatus();
    }
  }

  listServers(): ServerConfig[] {
    return loadConfig().servers;
  }

  async addServer(config: ServerConfig): Promise<void> {
    upsertServer(config);
    await registerConfiguredServers();
  }

  async removeServer(key: string): Promise<boolean> {
    return removeServerFromConfig(key);
  }

  /** Run the tunnel until it stops, reconnecting only on an UNEXPECTED throw.
   *
   * Tunnel.run() already loops internally over transient drops and returns only
   * when it stopped: a definitive 401 sets its `stopped` flag and returns (R6
   * auth exit), a REVOKE frame calls its stop() (same), and our own stop() sets
   * it too. So a clean return means one of two things, disambiguated by
   * intentionalStop:
   *   - intentionalStop=true  → we called stop(); done.
   *   - intentionalStop=false → the tunnel hit a 401/revoke; clear credentials,
   *     go unpaired, and wait for a user gesture. NEVER reconnect-loop a 401.
   * A throw is the only unexpected path; it gets a bounded backoff restart. */
  private async superviseLoop(): Promise<void> {
    let restartAttempts = 0;

    while (this.running && !this.intentionalStop) {
      const creds = loadCredentials();
      if (!creds?.refreshToken) {
        this.handleAuthExit();
        return;
      }

      this.tunnel = new Tunnel(creds);
      try {
        await this.tunnel.run();
      } catch (error) {
        this.logger.error(
          `[bridge] tunnel crashed unexpectedly: ${error instanceof Error ? error.message : String(error)}`,
        );
        if (this.intentionalStop) break;
        if (restartAttempts >= MAX_RESTART_ATTEMPTS) {
          this.logger.error(
            `[bridge] giving up after ${MAX_RESTART_ATTEMPTS} restart attempts`,
          );
          break;
        }
        restartAttempts += 1;
        this.logger.info(
          `[bridge] restarting tunnel (attempt ${restartAttempts}/${MAX_RESTART_ATTEMPTS})…`,
        );
        await delay(RESTART_DELAY_MS);
        continue;
      }

      // run() returned without throwing.
      if (this.intentionalStop) break;
      this.handleAuthExit();
      return;
    }

    this.tunnel = null;
    if (this.running) {
      this.running = false;
      this.emitStatus();
    }
  }

  /** The tunnel exited on an auth failure (401) or a revoke frame — the stored
   * credential is dead. Clear it so status() reports unpaired and a later user
   * gesture (re-pair, task 2.2) is required; do not reconnect. */
  private handleAuthExit(): void {
    this.logger.error(
      "[bridge] device no longer authorized (revoked or unpaired) — clearing credentials",
    );
    clearCredentials();
    this.tunnel = null;
    this.running = false;
    this.emitStatus();
  }

  private emitStatus(): void {
    this.events.emit(STATUS_EVENT, this.status());
  }
}

function delay(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

let instance: BridgeHost | null = null;

/** The process-wide BridgeHost singleton. A getter (not a module-level const) so
 * construction stays lazy and the host exists only once the bridge is used. */
export function getBridgeHost(): BridgeHost {
  if (!instance) instance = new BridgeHost();
  return instance;
}
