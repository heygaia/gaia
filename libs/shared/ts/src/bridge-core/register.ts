// Register every configured server with the cloud (creating its integration and
// enqueuing warm-connect). Split from serving so `gaia bridge add` can register a
// new server without starting a second tunnel.

import { exchangeToken, registerServer } from "./api.js";
import { loadConfig, loadCredentials, saveCredentials } from "./config.js";

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
