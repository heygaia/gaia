/**
 * electron-builder afterSign hook (macOS).
 *
 * Two mutually exclusive paths, chosen by whether real code signing ran:
 *
 * - Real signing DISABLED (CSC_IDENTITY_AUTO_DISCOVERY=false — dev/CI builds):
 *   the packaged app keeps only the Electron binary's linker signature with a
 *   broken bundle seal. macOS 26's RunningBoard kills LaunchServices-launched
 *   apps with an invalid seal ~12s after launch (Dock icon appears, then
 *   vanishes). Ad-hoc signing restores a valid seal so local Finder launches
 *   run. This path never touches notarization.
 *
 * - Real Developer-ID signing RAN (CSC_LINK/CSC_KEY_PASSWORD present): submit
 *   the signed app to Apple for notarization when the notarization credentials
 *   are set (APPLE_ID + APPLE_APP_SPECIFIC_PASSWORD + APPLE_TEAM_ID). Without a
 *   stable Developer-ID signature AND notarization, the TCC Full Disk Access
 *   grant resets on every rebuild (different cdhash), so this is the gate for
 *   the persistent-grant goal. Skipped with a warning when creds are absent.
 */
const { execFileSync } = require("node:child_process");
const path = require("node:path");

function adhocSign(appPath) {
  console.log(`  • ad-hoc signing (real signing disabled)  file=${appPath}`);
  // Absolute path to the SIP-protected system binary — never resolve via
  // $PATH, which a caller could repoint at a malicious `codesign`.
  execFileSync(
    "/usr/bin/codesign",
    ["--force", "--deep", "--sign", "-", appPath],
    { stdio: "inherit" },
  );
}

async function notarizeApp(context, appPath) {
  const appleId = process.env.APPLE_ID;
  const appleIdPassword = process.env.APPLE_APP_SPECIFIC_PASSWORD;
  const teamId = process.env.APPLE_TEAM_ID;
  if (!appleId || !appleIdPassword || !teamId) {
    console.warn(
      "  • notarization skipped — APPLE_ID / APPLE_APP_SPECIFIC_PASSWORD / APPLE_TEAM_ID not set",
    );
    return;
  }

  const { notarize } = require("@electron/notarize");
  console.log(`  • notarizing (notarytool)  file=${appPath}`);
  await notarize({ appPath, appleId, appleIdPassword, teamId });
}

module.exports = async function afterSign(context) {
  if (context.electronPlatformName !== "darwin") return;

  const appName = `${context.packager.appInfo.productFilename}.app`;
  const appPath = path.join(context.appOutDir, appName);

  if (process.env.CSC_IDENTITY_AUTO_DISCOVERY === "false") {
    adhocSign(appPath);
    return;
  }

  await notarizeApp(context, appPath);
};
