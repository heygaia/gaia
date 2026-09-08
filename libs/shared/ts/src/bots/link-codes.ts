/**
 * One-tap onboarding link codes.
 *
 * The web mints a code at the platform-pick step and the user carries it to the
 * bot — invisibly as a Telegram `?start=<code>` payload, visibly as a trailing
 * ` #<code>` on the WhatsApp/iMessage message they send. Redeeming it links the
 * account and returns the opening message, so nobody has to type `/auth`.
 *
 * Parsing and redemption live here, not per adapter: three platforms accepting
 * three slightly different code shapes is how one of them silently stops
 * matching.
 */

import type { GaiaClient } from "./api";
import { GaiaApiError } from "./api";
import type { MessageTarget, PlatformName } from "./types";
import { hashLogIdentifier } from "./utils/logger";
import { wideLog, withWideEvent } from "./utils/wide-events";

/**
 * Exact code width. `secrets.token_urlsafe(PLATFORM_LINK_CODE_BYTES)` with 16
 * bytes is always 22 urlsafe-base64 characters — see
 * `PLATFORM_LINK_CODE_BYTES` in `apps/api/app/constants/auth.py`, which must
 * change in the same commit as this.
 */
export const LINK_CODE_LENGTH = 22;

/**
 * A trailing `#<code>` and nothing after it. Anchored and length-exact so a
 * real hashtag never matches: `#launch` is 6 characters, and the alphabet is
 * the urlsafe-base64 one the API mints from.
 */
const TRAILING_LINK_CODE = new RegExp(
  `\\s*#([A-Za-z0-9_-]{${LINK_CODE_LENGTH}})\\s*$`,
);

export interface ParsedLinkCode {
  code: string;
  /** The message with the code (and its separator) removed. */
  text: string;
}

/** Splits a trailing ` #<code>` off a message, or null when there isn't one. */
export function parseTrailingLinkCode(message: string): ParsedLinkCode | null {
  const match = TRAILING_LINK_CODE.exec(message);
  if (!match) return null;
  return { code: match[1], text: message.slice(0, match.index).trim() };
}

export interface InboundLinkCodeArgs {
  gaia: GaiaClient;
  platform: PlatformName;
  platformUserId: string;
  /** The raw inbound message, possibly ending in ` #<code>`. */
  text: string;
  target: MessageTarget;
  /** Whether this handle is already linked to a GAIA account. */
  isLinked: () => Promise<boolean>;
  profile?: { username?: string; displayName?: string };
}

export interface InboundLinkCodeResult {
  /** The text to run through the normal chat flow. */
  text: string;
  /**
   * The text is the server-composed opener from a redemption, not something the
   * user typed. The adapter forwards it so the agent opens as a first contact.
   */
  onboardingHandoff: boolean;
}

/**
 * The WhatsApp/iMessage half of one-tap linking: the user's own first message
 * carries the code, so it must be redeemed and stripped before anything else
 * looks at the text.
 *
 * Returns the text to continue through the normal chat flow plus whether it came
 * out of a redemption, or null when there is nothing left to handle — the
 * redemption failed (the user already has a friendly explanation) or the message
 * was only a code.
 */
export async function consumeInboundLinkCode(
  args: InboundLinkCodeArgs,
): Promise<InboundLinkCodeResult | null> {
  const parsed = parseTrailingLinkCode(args.text);
  if (!parsed) return { text: args.text, onboardingHandoff: false };

  // An already-linked sender re-sending the prewritten message is not an error
  // worth a reply: drop the code and let the rest through.
  if (!(await args.isLinked())) {
    const redeemed = await redeemLinkCode(
      args.gaia,
      args.platform,
      args.platformUserId,
      parsed.code,
      args.target,
      args.profile,
    );
    if (redeemed === null) return null;
    // The server composed the opener from onboarding; it is the turn to run,
    // as on Telegram, even when the user edited the prewritten text. Only that
    // server-composed text is a handoff: the user's own edited message is
    // something they typed and watched send.
    if (redeemed) return { text: redeemed, onboardingHandoff: true };
    return parsed.text ? { text: parsed.text, onboardingHandoff: false } : null;
  }

  return parsed.text ? { text: parsed.text, onboardingHandoff: false } : null;
}

/** Sent when the code is stale, already used, or the handle belongs elsewhere. */
export function buildLinkCodeFailureMessage(
  reason: "expired" | "conflict" | "plan",
  frontendUrl: string,
): string {
  if (reason === "plan") {
    return (
      "**This platform is part of GAIA Pro**\n\n" +
      "Subscribe and tap the link again.\n" +
      `${frontendUrl}/pricing`
    );
  }
  if (reason === "conflict") {
    return (
      "**This account is already connected to someone else**\n\n" +
      "Disconnect it from the other GAIA account first, then try again.\n" +
      `${frontendUrl}/settings?section=linked-accounts`
    );
  }
  return (
    "**That link has expired**\n\n" +
    "Head back to GAIA and pick your platform again — it only takes a tap.\n" +
    `${frontendUrl}/onboarding`
  );
}

/**
 * Redeems `code` for `platformUserId`, returning the composed first message.
 *
 * On success it first sends the server-composed greeting to `target`, so the
 * user is greeted deterministically before the opener turn runs.
 *
 * On a failure the user can act on (expired/used code, handle already linked
 * elsewhere) it messages them and returns null — never a stack trace. Any other
 * failure propagates so it surfaces as a real error.
 */
export async function redeemLinkCode(
  gaia: GaiaClient,
  platform: PlatformName,
  platformUserId: string,
  code: string,
  target: MessageTarget,
  profile?: { username?: string; displayName?: string },
): Promise<string | null> {
  return withWideEvent(
    "link_code_redemption",
    {
      platform,
      component: "link-codes",
      user_hash: hashLogIdentifier(platformUserId),
    },
    async () => {
      try {
        const { firstMessage, greeting } = await gaia.redeemLinkCode(
          platform,
          platformUserId,
          code,
          profile,
        );
        // Hello first, then the opener turn. The greeting is the server's line
        // rather than the model's because the model kept skipping it, and the
        // ordering matters: the opener answers what the user picked, so it
        // arriving first reads like GAIA resuming a conversation nobody started.
        if (greeting) await target.send(greeting);
        wideLog.audit("platform_linked_via_code", {
          user_hash: hashLogIdentifier(platformUserId),
        });
        wideLog.set({ link_result: "linked" });
        return firstMessage;
      } catch (error: unknown) {
        const status = error instanceof GaiaApiError ? error.status : undefined;
        if (status !== 400 && status !== 409 && status !== 429) throw error;

        const reason =
          status === 409 ? "conflict" : status === 429 ? "plan" : "expired";
        wideLog.set({ link_result: "rejected", reason });
        wideLog.audit("platform_link_code_rejected", {
          user_hash: hashLogIdentifier(platformUserId),
          reason,
        });
        await target.send(
          buildLinkCodeFailureMessage(reason, gaia.getFrontendUrl()),
        );
        return null;
      }
    },
  );
}
