// Main font configuration file using Inter as the only font
import { inter } from "./inter";

// Export Inter font
export { inter };

// Set Inter as the default font
export const defaultFont = inter;

// The default text font (used for body text)
export const defaultTextFont = inter;

// Helper function to get font variables (only Inter now)
export function getAllFontVariables() {
  return inter.variable;
}
