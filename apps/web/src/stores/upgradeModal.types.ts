/**
 * The one payload the upgrade modal is opened with, whichever path opened it.
 *
 * Every field is optional because the call sites disagree on what they know:
 * a 402 `subscription_required` response carries `checkoutUrl`/`discountCode`/
 * `message` from the backend; the founder's letter carries a
 * `discountCode`/`discountPercent` pair (the percent lets the pricing cards
 * show what the reader will actually pay); and the plain "Upgrade to Pro"
 * buttons carry nothing at all.
 */
export interface UpgradeOffer {
  /** A personal Dodo checkout link minted by the backend, when it has one. */
  checkoutUrl?: string | null;
  /** Discount code to apply at checkout. */
  discountCode?: string | null;
  /** How much `discountCode` takes off, for the struck-through card prices. */
  discountPercent?: number | null;
  /** Overrides the modal's default body copy. */
  message?: string;
}

export interface UpgradeModalOptions {
  /** See `openModal`'s doc-comment for when to set this. Defaults to false. */
  dismissible?: boolean;
}

export interface UpgradeModalCloseOptions {
  /**
   * Close even when the modal is non-dismissible. For programmatic resets
   * only (the subscription flipped to paid, the desktop popup mirroring the
   * composer window) — never for a user-facing close control.
   */
  force?: boolean;
}
