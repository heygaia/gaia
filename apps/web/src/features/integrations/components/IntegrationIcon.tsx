import { PackageOpenIcon } from "@icons";
import { getToolCategoryIcon } from "@/features/chat/utils/toolIcons";

interface IntegrationIconProps {
  integrationId: string;
  iconUrl?: string | null;
  size?: number;
  showBackground?: boolean;
}

/**
 * Integration logo with a guaranteed fallback. Resolves a known category icon
 * or the integration's own `iconUrl`; when neither exists — e.g. a device MCP
 * server, which has no icon_url — it renders a generic package glyph instead of
 * a blank space. (getToolCategoryIcon returns null for the no-icon case by
 * design — the tool dropdown depends on that — so the fallback lives here.)
 */
export function IntegrationIcon({
  integrationId,
  iconUrl,
  size = 28,
  showBackground = false,
}: IntegrationIconProps) {
  const icon = getToolCategoryIcon(
    integrationId,
    { size, width: size, height: size, showBackground },
    iconUrl,
  );
  if (icon) return <>{icon}</>;

  const fallback = (
    <PackageOpenIcon width={size} height={size} className="text-zinc-400" />
  );
  return showBackground ? (
    <div className="flex aspect-square items-center justify-center rounded-lg bg-zinc-700 p-1">
      {fallback}
    </div>
  ) : (
    fallback
  );
}
