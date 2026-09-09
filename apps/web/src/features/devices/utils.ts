import { PAIRING_CODE_LENGTH } from "./constants";

/**
 * Normalize a raw pairing code (from the `?code=` param or a paste) into the
 * separator-less, uppercase digits the code field holds. Strips the separator
 * the daemon prints (e.g. "NS2V-YC5S" -> "NS2VYC5S") so a code copied straight
 * from chat pastes cleanly.
 */
export function normalizePairingCode(raw: string): string {
  return raw
    .toUpperCase()
    .replace(/[^A-Z0-9]/g, "")
    .slice(0, PAIRING_CODE_LENGTH);
}
