import { describe, expect, it } from "vitest";

import { assertLoopbackUrl } from "../../src/commands/bridge/servers.js";

// A url server must point at THIS machine — otherwise the cloud could drive the
// daemon into the user's LAN (SSRF pivot). Config is user-editable, so this guard
// runs on save and on open.
describe("assertLoopbackUrl", () => {
  it.each([
    "http://localhost:9000/mcp",
    "http://127.0.0.1:8080/mcp",
    "https://localhost/mcp",
    "http://[::1]:3000/mcp",
  ])("accepts loopback %s", (url) => {
    expect(() => assertLoopbackUrl(url)).not.toThrow();
  });

  it.each([
    "http://192.168.1.5/mcp",
    "https://example.com/mcp",
    "http://10.0.0.1:9000/mcp",
    "http://169.254.169.254/mcp",
  ])("rejects non-loopback %s", (url) => {
    expect(() => assertLoopbackUrl(url)).toThrow(/this machine/);
  });

  it("rejects a non-http(s) scheme", () => {
    expect(() => assertLoopbackUrl("ftp://localhost/mcp")).toThrow(/http/);
  });
});
