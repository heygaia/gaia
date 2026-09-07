/**
 * The import-logins modal hands the user one command to paste. These pin the
 * pieces that must be exactly right for it to work against any deployment:
 * the bare origin the tool is pointed at, when that override is (and isn't)
 * spelled out, the npx form of the command, and the countdown that tells the
 * user the code is still live.
 */
import { describe, expect, it } from "vitest";
import {
  buildConnectCommand,
  connectApiOrigin,
  connectApiOverride,
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

describe("connectApiOverride", () => {
  it("is null on production, where the tool's default already matches", () => {
    expect(connectApiOverride("https://api.heygaia.io/api/v1/")).toBeNull();
  });

  it("names the origin for dev and self-hosted APIs", () => {
    expect(connectApiOverride("http://localhost:8510/api/v1/")).toBe(
      "http://localhost:8510",
    );
  });
});

describe("buildConnectCommand", () => {
  it("is the short npx form when no API override is needed", () => {
    expect(buildConnectCommand({ token: "abc123", apiOrigin: null })).toBe(
      "npx @heygaia/cli connect --token abc123",
    );
  });

  it("appends --api only when an override was given", () => {
    expect(
      buildConnectCommand({
        token: "abc123",
        apiOrigin: "http://localhost:8510",
      }),
    ).toBe(
      "npx @heygaia/cli connect --token abc123 --api http://localhost:8510",
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
