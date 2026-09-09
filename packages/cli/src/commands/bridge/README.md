# gaia bridge

Outbound-only tunnel daemon: pairs a machine with a GAIA account and exposes local MCP servers / folders to the cloud over one WebSocket, no inbound ports. Full design: `.agents/plans/device-bridge-and-local-mcp-design.md` (gitignored) and the `device-bridge-local-mcp` memory. Backend counterpart lives in `apps/api/app/services/device/` and `app/services/mcp/device_connector.py`.

Normal usage is interactive (`gaia bridge login` opens a browser for RFC 8628 pairing, `gaia bridge add` is a guided wizard) — see `gaia bridge help`. The rest of this doc covers testing the tunnel itself without going through that UI.

## Usage

One flow takes a machine from nothing to working tools:

```bash
gaia bridge login      # pair this machine (opens a browser to approve)
gaia bridge add        # guided wizard — connect a server or expose folders
gaia bridge up         # hold the outbound tunnel (Ctrl+C to stop)
gaia bridge ls         # pairing status + configured servers
gaia bridge rm <key>   # remove one configured server
gaia bridge logout     # forget local credentials on this machine
```

Config and credentials live under `~/.gaia/bridge/` (`config.json`, `credentials.json`, both `0600`). Point the CLI at a non-prod API with `--api` on `login`, or `GAIA_API_URL=…` in the environment (defaults to `https://api.heygaia.io`).

### `gaia bridge add` — the guided wizard

After pairing, the wizard connects any of **three** kinds of thing:

1. **A command that starts an MCP server (stdio)** — e.g. `npx -y @modelcontextprotocol/server-everything`, `uvx some-server`, `docker run -i --rm my/image`. The wizard captures any required env vars/secrets (stored `0600`, never leave the machine) and verifies the server starts and lists tools before saving.
2. **An MCP server already running at a local URL** — e.g. `http://localhost:3000/mcp`. Must be loopback (`localhost`/`127.0.0.1`/`::1`); optional request headers (e.g. `Authorization`) are stored `0600`.
3. **Local files & folders — no MCP needed.** Exposes the **built-in filesystem server** (`list_directory`, `read_file`, `search_files`, plus `write_file` if you allow writes). You choose:
   - **Specific folders** (space-separated, `~` expands, quote paths with spaces), or **your entire filesystem** (everything this user account can read — the wizard warns first, since that includes things like `~/.ssh`).
   - **Read-only** (default) or **read/write**.

Everything the agent can reach is contained to the approved roots: every path is `realpath`-resolved and must live inside an approved folder (symlink escapes are refused), so "specific folders" cannot be walked out of.

### `gaia bridge fs` — folders in one shot (no wizard)

Same built-in filesystem server, non-interactive:

```bash
gaia bridge fs ~/Documents ~/code      # read-only access to these folders
gaia bridge fs --write ~/notes         # allow GAIA to modify files here too
```

Then `gaia bridge up`. There is one filesystem server per device (stable key `filesystem`); re-running `fs` (or re-choosing it in the wizard) replaces its folder list. The wizard's "entire filesystem" option has no `fs` flag — use the wizard for that.

## Automated tests

- `apps/api/tests/integration/real/test_device_bridge_e2e.py` — **the real thing, black-box.** Spawns this daemon as a real subprocess (via `tsx`, no build step) against a real, live GAIA API instance bound to a real localhost port, pairs it through the actual RFC 8628 flow, exposes the real `@modelcontextprotocol/server-everything` reference server over real stdio (the general third-party-server path, not the built-in `filesystem` special case), drives a real MCP handshake + `tools/list` through the whole tunnel via `POST /mcp/test/{integration_id}`, then revokes the device over real HTTP and asserts the daemon drops its own socket. Nothing here is mocked or called into directly — every step is the exact wire traffic a real user's browser and machine produce. It also asserts no `reconnecting in …ms` line ever appears — the regression guard for the historical bug below. Run: `cd apps/api && uv run pytest tests/integration/real/test_device_bridge_e2e.py -v -n0` (needs `nx run docker:docker:up` for Postgres/Redis/Mongo, `pnpm install` for the CLI package's `node_modules`, and network access — the reference server is fetched via `npx` on first run). See `apps/api/tests/integration/real/README.md` for the fixture design (`live_api_server`, `HeaderDrivenAuthMiddleware`).
- `apps/api/tests/integration/real/test_device_bridge_real.py` — a narrower, lower-level tier: the Python side's internal plumbing (presence ownership, up-channel routing, revoke-listener targeting, a `DeviceConnector` round trip against a fake in-process daemon) against real Redis, for regression-testing specific bugs in isolation without the cost of a real subprocess. Run: `uv run pytest tests/integration/real/test_device_bridge_real.py -v`.
- `apps/api/tests/unit/services/test_mcp_client.py::TestMCPClientBuildDeviceClient` — the cross-user ownership gate (a device session must never build for a device the caller doesn't own).

The historical bug worth knowing about: `tunnel.ts`'s `connectOnce()` once resolved its connection promise on the socket's `open` event instead of `close`, so `run()` immediately looped and opened a new socket on every tick — an infinite reconnect storm that only a real socket (not a mock) could have surfaced. `test_device_bridge_e2e.py` now guards against a regression of exactly that.

## Manual exploration

For interactively poking at the tunnel outside of the automated suite: `nx run docker:docker:up`, then `nx dev api` (or `mise dev`), then run this daemon for real from `packages/cli` (`pnpm tsx src/index.ts bridge …`) — `gaia bridge login` (or `login --api http://localhost:8000 --name my-test-machine`) followed by `gaia bridge add` (or `gaia bridge fs <dir>` for the built-in filesystem server) and `gaia bridge up`. Approve the pairing from `http://localhost:3000/settings/devices/approve` (prefilled if you follow the printed link). Use a scratch `HOME` env var if you don't want this to touch your real paired-device credentials.
