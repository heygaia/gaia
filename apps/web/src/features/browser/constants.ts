/** Mirrors `BROWSER_PROFILE_TTL_DAYS` in apps/api/app/constants/browser.py —
 * saved-site session data auto-expires this long after its last use. */
export const SAVED_LOGIN_TTL_DAYS = 90;

/** Where the local `gaia-connect` tool lives until it ships as a download. */
export const GAIA_CONNECT_README_URL =
  "https://github.com/theexperiencecompany/gaia/tree/master/tools/gaia-connect";

/** Browsers `gaia-connect` can read today (macOS, Chromium family). Offered
 * in the picker so the command carries `--browser` and skips the tool's own
 * prompt; anything else Chromium-based still works via detection. */
export const CONNECTABLE_BROWSERS = ["Arc", "Chrome", "Edge"] as const;
export type ConnectableBrowser = (typeof CONNECTABLE_BROWSERS)[number];
