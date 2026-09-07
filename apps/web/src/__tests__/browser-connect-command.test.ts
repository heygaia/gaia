/**
 * The Connect-browser modal hands the user one command to paste. These pin
 * the pieces that must be exactly right for it to work against any deployment:
 * the API origin the tool talks to, the flags it accepts (`--api`, `--token`,
 * `--browser`), and the countdown that tells the user the code is still live.
 */
import { describe, expect, it } from "vitest";
import {
  buildConnectCommand,
  connectApiOrigin,
  formatCountdown,
} from "@/features/browser/utils";

describe("connectApiOrigin", () => {
  it("strips the /api/v1 path so the tool gets a bare origin", () => {
    expect(connectApiOrigin("http://localhost:8510/api/v1/")).toBe(
      "http://localhost:8510",
    );
    expect(connectApiOrigin("https://api.example.com/api/v1")).toBe(
      "https://api.example.com",
    );
  });
});

describe("buildConnectCommand", () => {
  it("carries the origin and the code", () => {
    expect(
      buildConnectCommand({
        apiOrigin: "https://api.example.com",
        token: "abc123",
        browser: null,
      }),
    ).toBe("gaia-connect --api https://api.example.com --token abc123");
  });

  it("adds --browser only when one was picked", () => {
    expect(
      buildConnectCommand({
        apiOrigin: "https://api.example.com",
        token: "abc123",
        browser: "Arc",
      }),
    ).toBe(
      "gaia-connect --api https://api.example.com --token abc123 --browser Arc",
    );
  });
});

describe("formatCountdown", () => {
  it("renders m:ss with a padded seconds field", () => {
    expect(formatCountdown(598)).toBe("9:58");
    expect(formatCountdown(65)).toBe("1:05");
  });

  it("never goes negative once the code has expired", () => {
    expect(formatCountdown(0)).toBe("0:00");
    expect(formatCountdown(-30)).toBe("0:00");
  });
});
