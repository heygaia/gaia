/**
 * One-tap onboarding link codes.
 *
 * The web mints a code at the platform-pick step and the user carries it to the
 * bot — invisibly as a Telegram `?start=<code>` payload, visibly as a trailing
 * ` #<code>` on the WhatsApp/iMessage message they send. Redeeming it links the
 * account AND sends GAIA's whole first contact, so nobody has to type `/auth`
 * and no model turn stands between linking and the first real message.
 *
 * Parsing and redemption live here, not per adapter: three platforms accepting
 * three slightly different code shapes is how one of them silently stops
 * matching.
 */

import type { GaiaClient } from "./api";
import { GaiaApiError } from "./api";
import type { MessageTarget, PlatformName } from "./types";
import { createBotLogger, hashLogIdentifier } from "./utils/logger";
import { wideLog, withWideEvent } from "./utils/wide-events";

const logger = createBotLogger("shared", "link-codes");

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

/**
 * The WhatsApp/iMessage half of one-tap linking: the user's own first message
 * carries the code, so it must be redeemed and stripped before anything else
 * looks at the text.
 *
 * Returns the text to continue through the normal chat flow, or null when there
 * is nothing left to handle: an unlinked sender's code was redeemed (GAIA's
 * first contact IS the reply) or refused (they already have the explanation),
 * or a linked sender's message was nothing but a stray code.
 */
export async function consumeInboundLinkCode(
  args: InboundLinkCodeArgs,
): Promise<string | null> {
  const parsed = parseTrailingLinkCode(args.text);
  if (!parsed) return args.text;

  // An already-linked sender re-sending the prewritten message is not an error
  // worth a reply: drop the code and let the rest through.
  if (!(await args.isLinked())) {
    // Either outcome ends the turn. A success has already delivered the whole
    // first contact, so running the stripped text on top of it would answer the
    // user's own prewritten opener a second time; a failure has already told
    // them why, and chatting past it strands them mid-explanation.
    await redeemLinkCode(
      args.gaia,
      args.platform,
      args.platformUserId,
      parsed.code,
      args.target,
      args.profile,
    );
    return null;
  }

  return parsed.text || null;
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
 * Redeems `code` for `platformUserId` and delivers GAIA's first contact.
 *
 * The API composes every bubble — the hello, one promise per thing the user
 * picked at onboarding, then the connect links — and this sends them in order
 * through `target`. No model turn runs: the opener turn used to skip the
 * per-pick lines and lose the links, and the one message a new user is
 * guaranteed to read does not get to be unreliable.
 *
 * Returns true once the bubbles are out. On a failure the user can act on
 * (expired/used code, handle already linked elsewhere) it messages them and
 * returns false — never a stack trace. Any other failure propagates so it
 * surfaces as a real error.
 */
/**
 * Sends bubbles strictly one after another, never fanned out: they are a
 * conversation, and arriving out of order reads as GAIA talking over itself.
 * Emits the same `bubble_delivered` line the streamer emits per finished
 * bubble, so a first contact and a normal reply look identical in Loki.
 */
function deliverInOrder(
  bubbles: readonly string[],
  send: (bubble: string) => Promise<unknown>,
): Promise<number> {
  const queue = bubbles.filter((bubble) => bubble.trim());
  const deliver = (index: number): Promise<number> => {
    const bubble = queue[index];
    if (bubble === undefined) return Promise.resolve(index);
    return send(bubble).then(() => {
      logger.info("bubble_delivered", {
        method: "new",
        index,
        chars: bubble.length,
      });
      return deliver(index + 1);
    });
  };
  return deliver(0);
}

export async function redeemLinkCode(
  gaia: GaiaClient,
  platform: PlatformName,
  platformUserId: string,
  code: string,
  target: MessageTarget,
  profile?: { username?: string; displayName?: string },
): Promise<boolean> {
  return withWideEvent(
    "link_code_redemption",
    {
      platform,
      component: "link-codes",
      user_hash: hashLogIdentifier(platformUserId),
    },
    async () => {
      try {
        const { bubbles } = await gaia.redeemLinkCode(
          platform,
          platformUserId,
          code,
          profile,
        );
        await deliverInOrder(bubbles, (bubble) => target.send(bubble));
        wideLog.audit("platform_linked_via_code", {
          user_hash: hashLogIdentifier(platformUserId),
        });
        wideLog.set({ link_result: "linked", bubbles: bubbles.length });
        return true;
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
        return false;
      }
    },
  );
}
