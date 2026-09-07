"use client";

import { NOTIFICATION_CHANNELS } from "@gaia/shared";
import type { ChannelPlatform, ChannelPreferences } from "@gaia/shared/types";
import { Switch } from "@heroui/switch";
import Image from "next/image";
import { useEffect, useState } from "react";
import { isBotPlatform } from "@/config/botPlatforms";
import {
  NOTIFICATION_CHANNEL_ICONS,
  NOTIFICATION_CHANNEL_LABELS,
} from "@/features/notification/constants";
import { SettingsPage } from "@/features/settings/components/ui/SettingsPage";
import { SettingsRow } from "@/features/settings/components/ui/SettingsRow";
import { SettingsSection } from "@/features/settings/components/ui/SettingsSection";
import { apiService } from "@/lib/api/service";
import { toast } from "@/lib/toast";
import { NotificationsAPI } from "@/services/api/notifications";
import type { PlatformLink } from "@/types/platform";

export default function NotificationSettings() {
  const [platformLinks, setPlatformLinks] = useState<
    Record<string, PlatformLink | null>
  >({});
  const [channelPrefs, setChannelPrefs] = useState<ChannelPreferences>(
    () =>
      Object.fromEntries(
        NOTIFICATION_CHANNELS.map((channel) => [channel, true]),
      ) as ChannelPreferences,
  );
  const [loading, setLoading] = useState(true);
  const [togglingPlatform, setTogglingPlatform] = useState<string | null>(null);

  useEffect(() => {
    const fetchAll = async () => {
      setLoading(true);
      try {
        const [linksData, prefs] = await Promise.all([
          apiService.get<{
            platform_links: Record<string, PlatformLink | null>;
          }>("/platform-links", { silent: true }),
          NotificationsAPI.getChannelPreferences(),
        ]);
        setPlatformLinks(linksData.platform_links || {});
        setChannelPrefs(prefs);
      } catch {
        // silently ignore
      } finally {
        setLoading(false);
      }
    };

    fetchAll();
  }, []);

  const handleToggle = async (channel: ChannelPlatform, enabled: boolean) => {
    setTogglingPlatform(channel);
    try {
      await NotificationsAPI.updateChannelPreference(channel, enabled);
      setChannelPrefs((prev) => ({ ...prev, [channel]: enabled }));
    } catch {
      toast.error(`Failed to update ${channel} notification preference`);
    } finally {
      setTogglingPlatform(null);
    }
  };

  return (
    <SettingsPage>
      <SettingsSection description="Choose where to receive GAIA notifications.">
        {NOTIFICATION_CHANNELS.map((channel) => {
          const label = NOTIFICATION_CHANNEL_LABELS[channel];
          // Only bot platforms need a linked account; email reaches the user
          // through the address on their GAIA account.
          const needsLink = isBotPlatform(channel);
          const isAvailable =
            !needsLink || !!platformLinks[channel]?.platformUserId;
          return (
            <SettingsRow
              key={channel}
              label={label}
              description={
                isAvailable
                  ? "Send notifications to this channel"
                  : "Connect in Linked Accounts to enable"
              }
              icon={
                <Image
                  src={NOTIFICATION_CHANNEL_ICONS[channel]}
                  alt={label}
                  width={36}
                  height={36}
                  className="rounded-xl"
                />
              }
            >
              <Switch
                size="sm"
                isSelected={isAvailable ? channelPrefs[channel] : false}
                isDisabled={
                  !isAvailable || loading || togglingPlatform === channel
                }
                onValueChange={(enabled) => handleToggle(channel, enabled)}
                aria-label={`Enable ${label} notifications`}
              />
            </SettingsRow>
          );
        })}
      </SettingsSection>
    </SettingsPage>
  );
}
