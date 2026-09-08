/**
 * One-tap onboarding link codes.
 *
 * These pin the two things that break silently in production: the trailing
 * `#<code>` regex (too loose and it eats a real hashtag; too tight and linking
 * never fires) and the unlinked-vs-linked branching that decides whether a
 * redemption is attempted at all.
 */

import type { GaiaClient, MessageTarget } from "@gaia/shared/bots";
import {
  buildLinkCodeFailureMessage,
  consumeInboundLinkCode,
  GaiaApiError,
  LINK_CODE_LENGTH,
  parseTrailingLinkCode,
  redeemLinkCode,
} from "@gaia/shared/bots";
import { describe, expect, it, vi } from "vitest";

/** A real-shaped code: 22 urlsafe-base64 characters. */
const CODE = "Ab3-_xY9zQ1234567890wE";
const FIRST_MESSAGE =
  "Hi! I'm a founder. I could use help with my inbox. Who are you?";
const FRONTEND_URL = "https://gaia.test";
/** What the API composes: hello, one promise per pick, then the first move. */
const BUBBLES = [
  "Hey Aryan. I'm with you on WhatsApp now.",
  "Your inbox is out of control. Every morning I'll have it sorted and the replies drafted.",
  "One tap and that switches on. The link is live for the next hour:",
  "Gmail: https://gaia.test/connect/abc",
];
const okRedeem = () => vi.fn(async () => ({ linked: true, bubbles: BUBBLES }));

function fakeTarget(): MessageTarget & { sent: string[] } {
  const sent: string[] = [];
  return {
    sent,
    platform: "whatsapp",
    send: vi.fn(async (text: string) => {
      sent.push(text);
      return { id: "1", edit: async () => undefined };
    }),
    sendEphemeral: vi.fn(async (text: string) => {
      sent.push(text);
      return { id: "1", edit: async () => undefined };
    }),
    startTyping: vi.fn(async () => () => undefined),
  } as unknown as MessageTarget & { sent: string[] };
}

function fakeGaia(redeem: unknown): GaiaClient {
  return {
    redeemLinkCode: redeem,
    getFrontendUrl: () => FRONTEND_URL,
  } as unknown as GaiaClient;
}

describe("parseTrailingLinkCode", () => {
  it("splits the code off the end and trims the separator", () => {
    expect(parseTrailingLinkCode(`${FIRST_MESSAGE} #${CODE}`)).toEqual({
      code: CODE,
      text: FIRST_MESSAGE,
    });
  });

  it("tolerates trailing whitespace after the code", () => {
    expect(parseTrailingLinkCode(`hello #${CODE}  `)).toEqual({
      code: CODE,
      text: "hello",
    });
  });

  it("matches a message that is only a code", () => {
    expect(parseTrailingLinkCode(`#${CODE}`)).toEqual({ code: CODE, text: "" });
  });

  it("does not match a real hashtag", () => {
    expect(parseTrailingLinkCode("shipping today #launch")).toBeNull();
    expect(parseTrailingLinkCode("#todo remind me to call mum")).toBeNull();
  });

  it("does not match a token of the wrong length", () => {
    expect(parseTrailingLinkCode(`hi #${CODE.slice(0, -1)}`)).toBeNull();
    expect(parseTrailingLinkCode(`hi #${CODE}x`)).toBeNull();
  });

  it("does not match a token outside the code alphabet", () => {
    expect(
      parseTrailingLinkCode(`hi #${"a".repeat(LINK_CODE_LENGTH - 1)}!`),
    ).toBeNull();
  });

  it("only matches at the end of the message", () => {
    expect(parseTrailingLinkCode(`#${CODE} and then some`)).toBeNull();
  });

  it("returns null when there is no code at all", () => {
    expect(parseTrailingLinkCode(FIRST_MESSAGE)).toBeNull();
  });
});

describe("redeemLinkCode", () => {
  it("delivers every bubble the server composed and reports success", async () => {
    const redeem = okRedeem();
    const target = fakeTarget();

    const result = await redeemLinkCode(
      fakeGaia(redeem),
      "telegram",
      "TG42",
      CODE,
      target,
      { username: "tg_user" },
    );

    expect(result).toBe(true);
    expect(redeem).toHaveBeenCalledWith("telegram", "TG42", CODE, {
      username: "tg_user",
    });
    expect(target.sent).toEqual(BUBBLES);
  });

  it("skips a blank bubble rather than sending an empty message", async () => {
    // Platform send APIs reject empty text, and one bad bubble must not take
    // the whole first contact down with it.
    const redeem = vi.fn(async () => ({
      linked: true,
      bubbles: [BUBBLES[0], "   ", BUBBLES[1]],
    }));
    const target = fakeTarget();

    await redeemLinkCode(fakeGaia(redeem), "telegram", "TG42", CODE, target);

    expect(target.sent).toEqual([BUBBLES[0], BUBBLES[1]]);
  });

  it("resolves only after the last bubble is out", async () => {
    // The adapter stops its typing indicator on this promise; resolving early
    // leaves the rest of the first contact landing after "typing" stopped.
    const target = fakeTarget();

    const result = await redeemLinkCode(
      fakeGaia(okRedeem()),
      "telegram",
      "TG42",
      CODE,
      target,
    );

    expect(result).toBe(true);
    expect(target.send).toHaveBeenCalledTimes(BUBBLES.length);
  });

  it("explains an expired code instead of throwing", async () => {
    const redeem = vi.fn(async () => {
      throw new GaiaApiError("API error: 400", 400);
    });
    const target = fakeTarget();

    const result = await redeemLinkCode(
      fakeGaia(redeem),
      "whatsapp",
      "WA1",
      CODE,
      target,
    );

    expect(result).toBe(false);
    expect(target.sent).toEqual([
      buildLinkCodeFailureMessage("expired", FRONTEND_URL),
    ]);
    expect(target.sent[0]).toContain("expired");
  });

  it("explains an account already linked elsewhere", async () => {
    const redeem = vi.fn(async () => {
      throw new GaiaApiError("API error: 409", 409);
    });
    const target = fakeTarget();

    const result = await redeemLinkCode(
      fakeGaia(redeem),
      "whatsapp",
      "WA1",
      CODE,
      target,
    );

    expect(result).toBe(false);
    expect(target.sent).toEqual([
      buildLinkCodeFailureMessage("conflict", FRONTEND_URL),
    ]);
    expect(target.sent[0]).toContain("already connected to someone else");
  });

  it("points a free user at pricing instead of throwing on a paid platform", async () => {
    const redeem = vi.fn(async () => {
      throw new GaiaApiError("API error: 429", 429);
    });
    const target = fakeTarget();

    const result = await redeemLinkCode(
      fakeGaia(redeem),
      "whatsapp",
      "WA1",
      CODE,
      target,
    );

    expect(result).toBe(false);
    expect(target.sent).toEqual([
      buildLinkCodeFailureMessage("plan", FRONTEND_URL),
    ]);
    expect(target.sent[0]).toContain(`${FRONTEND_URL}/pricing`);
  });

  it("sends no bubble at all when the redemption failed", async () => {
    const target = fakeTarget();
    const redeem = vi.fn(async () => {
      throw new GaiaApiError("API error: 400", 400);
    });

    await redeemLinkCode(fakeGaia(redeem), "telegram", "TG42", CODE, target);

    for (const bubble of BUBBLES) expect(target.sent).not.toContain(bubble);
  });

  it("lets an unexpected failure propagate rather than faking a link", async () => {
    const redeem = vi.fn(async () => {
      throw new GaiaApiError("API error: 500", 500);
    });
    const target = fakeTarget();

    await expect(
      redeemLinkCode(fakeGaia(redeem), "whatsapp", "WA1", CODE, target),
    ).rejects.toThrow(GaiaApiError);
    expect(target.sent).toEqual([]);
  });
});

describe("consumeInboundLinkCode", () => {
  const base = (overrides: Record<string, unknown>) => ({
    platform: "whatsapp" as const,
    platformUserId: "WA1",
    target: fakeTarget(),
    ...overrides,
  });

  it("passes a codeless message straight through and never calls the API", async () => {
    const redeem = vi.fn();
    const isLinked = vi.fn(async () => false);

    const result = await consumeInboundLinkCode(
      base({
        gaia: fakeGaia(redeem),
        text: "what's on my calendar?",
        isLinked,
      }),
    );

    expect(result).toBe("what's on my calendar?");
    expect(redeem).not.toHaveBeenCalled();
    expect(isLinked).not.toHaveBeenCalled();
  });

  it("redeems for an unlinked sender and leaves no turn to run", async () => {
    // The bundle IS the reply. Returning the stripped text here would answer the
    // user's own prewritten opener a second time, underneath a reply that
    // already covers everything they picked.
    const redeem = okRedeem();
    const target = fakeTarget();

    const result = await consumeInboundLinkCode(
      base({
        gaia: fakeGaia(redeem),
        text: `${FIRST_MESSAGE} #${CODE}`,
        isLinked: async () => false,
        target,
      }),
    );

    expect(result).toBeNull();
    expect(redeem).toHaveBeenCalledOnce();
    expect(target.sent).toEqual(BUBBLES);
  });

  it("does not greet when the inbound redemption fails", async () => {
    const redeem = vi.fn(async () => {
      throw new GaiaApiError("API error: 409", 409);
    });
    const target = fakeTarget();

    await consumeInboundLinkCode(
      base({
        gaia: fakeGaia(redeem),
        text: `${FIRST_MESSAGE} #${CODE}`,
        isLinked: async () => false,
        target,
      }),
    );

    expect(target.sent).toEqual([
      buildLinkCodeFailureMessage("conflict", FRONTEND_URL),
    ]);
  });

  it("delivers the bundle even when the user edited the prewritten text", async () => {
    const target = fakeTarget();

    const result = await consumeInboundLinkCode(
      base({
        gaia: fakeGaia(okRedeem()),
        text: `hi #${CODE}`,
        isLinked: async () => false,
        target,
      }),
    );

    expect(result).toBeNull();
    expect(target.sent).toEqual(BUBBLES);
  });

  it("strips a stray code from a linked sender without redeeming or replying", async () => {
    const redeem = vi.fn();
    const target = fakeTarget();

    const result = await consumeInboundLinkCode(
      base({
        gaia: fakeGaia(redeem),
        text: `remind me tomorrow #${CODE}`,
        isLinked: async () => true,
        target,
      }),
    );

    expect(result).toBe("remind me tomorrow");
    expect(redeem).not.toHaveBeenCalled();
    expect(target.sent).toEqual([]);
  });

  it("stops the turn when redemption fails", async () => {
    const redeem = vi.fn(async () => {
      throw new GaiaApiError("API error: 400", 400);
    });

    const result = await consumeInboundLinkCode(
      base({
        gaia: fakeGaia(redeem),
        text: `${FIRST_MESSAGE} #${CODE}`,
        isLinked: async () => false,
      }),
    );

    expect(result).toBeNull();
  });

  it("delivers the bundle when the message was nothing but a code", async () => {
    const redeem = okRedeem();
    const target = fakeTarget();

    const result = await consumeInboundLinkCode(
      base({
        gaia: fakeGaia(redeem),
        text: `#${CODE}`,
        isLinked: async () => false,
        target,
      }),
    );

    expect(result).toBeNull();
    expect(redeem).toHaveBeenCalledOnce();
    expect(target.sent).toEqual(BUBBLES);
  });

  it("sends every bubble in the order the server composed them", async () => {
    // These are a conversation: out of order, GAIA talks over itself and the
    // connect link arrives before the promise that explains what it is for.
    const target = fakeTarget();

    await consumeInboundLinkCode(
      base({
        gaia: fakeGaia(okRedeem()),
        text: `#${CODE}`,
        isLinked: async () => false,
        target,
      }),
    );

    expect(target.sent).toEqual(BUBBLES);
    expect(target.send).toHaveBeenCalledTimes(BUBBLES.length);
  });
});
