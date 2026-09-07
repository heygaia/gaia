/** Mirrors `BROWSER_PROFILE_TTL_DAYS` in apps/api/app/constants/browser.py —
 * saved-site session data auto-expires this long after its last use. */
export const SAVED_LOGIN_TTL_DAYS = 90;

/** The API the `gaia connect` tool talks to unless told otherwise — mirrors the
 * `--api` default in tools/gaia-connect/flags.go. The modal only spells out
 * `--api` when the web's own API origin differs (dev, self-hosted). */
export const GAIA_CONNECT_DEFAULT_API_ORIGIN = "https://api.heygaia.io";
