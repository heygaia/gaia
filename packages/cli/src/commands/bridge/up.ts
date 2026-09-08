// `gaia bridge up` — register configured servers with the cloud and hold the tunnel.

import { exchangeToken, registerServer } from "./api.js";
import {
  getFilesystemServer,
  loadConfig,
  loadCredentials,
  saveCredentials,
} from "./config.js";
import { Tunnel } from "./tunnel.js";

/** Register every configured server with the cloud (creating its integration and
 * enqueuing warm-connect). Split from serving so `gaia bridge add` can register a
 * new server without starting a second tunnel. */
export async function registerConfiguredServers(): Promise<void> {
  const creds = loadCredentials();
  if (!creds?.refreshToken)
    throw new Error("not paired — run: gaia bridge login");
  const servers = loadConfig().servers;
  if (servers.length === 0) {
    throw new Error("no servers configured — run: gaia bridge add");
  }
  const token = await exchangeToken(creds.apiUrl, creds.refreshToken);
  // Persist the rotated token before anything else can use the old one.
  saveCredentials({ ...creds, refreshToken: token.refresh_token });
  // Independent registrations that all share the one already-exchanged access
  // token — register them concurrently rather than one round trip at a time.
  await Promise.all(
    servers.map((server) =>
      registerServer(
        creds.apiUrl,
        token.access_token,
        server.key,
        server.name,
        server.type,
      ),
    ),
  );
}

export async function runUp(): Promise<void> {
  if (getFilesystemServer()?.allowWrite) {
    console.error(
      "[gaia bridge] filesystem WRITES are enabled for this device.",
    );
  }
  const urlWithHeaders = loadConfig().servers.filter(
    (s) => s.type === "url" && s.headers && Object.keys(s.headers).length > 0,
  );
  if (urlWithHeaders.length > 0) {
    console.error(
      `[gaia bridge] forwarding request headers (credentials) to ${urlWithHeaders.length} local url server(s).`,
    );
  }

  await registerConfiguredServers();
  const creds = loadCredentials();
  if (!creds?.refreshToken)
    throw new Error("not paired — run: gaia bridge login");

  const tunnel = new Tunnel(creds);
  const shutdown = async () => {
    console.error("\n[gaia bridge] shutting down…");
    await tunnel.stop();
    process.exit(0);
  };
  process.on("SIGINT", () => void shutdown());
  process.on("SIGTERM", () => void shutdown());
  await tunnel.run();
}
