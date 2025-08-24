/**
 * Timezone utilities for displaying timezone information with offsets
 */
import moment from "moment-timezone";

export interface TimezoneInfo {
  value: string;
  label: string;
  offset: string;
  abbreviation: string;
  formattedLabel: string;
  currentTime: string;
}

/**
 * Get timezone information including UTC offset and abbreviation using moment
 */
export const getTimezoneInfo = (timezone: string): TimezoneInfo => {
  try {
    const now = moment.tz(timezone);
    const offset = now.format("Z"); // e.g., "+05:30", "-05:00"
    const abbreviation = now.format("z"); // e.g., "PST", "IST"
    const currentTime = now.format("HH:mm");

    // Get clean city name
    const cityName = getTimezoneDisplayName(timezone);

    return {
      value: timezone,
      label: cityName,
      offset,
      abbreviation,
      currentTime,
      formattedLabel: `${cityName} (UTC${offset}) - ${currentTime}`,
    };
  } catch (error) {
    console.warn(`Error getting timezone info for ${timezone}:`, error);
    return {
      value: timezone,
      label: timezone,
      offset: "+00:00",
      abbreviation: "",
      currentTime: "--:--",
      formattedLabel: timezone,
    };
  }
};

/**
 * Get human-readable timezone display name
 */
const getTimezoneDisplayName = (timezone: string): string => {
  // Common timezone name mappings for better UX
  const cityMap: Record<string, string> = {
    UTC: "UTC",
    "America/New_York": "New York",
    "America/Chicago": "Chicago",
    "America/Denver": "Denver",
    "America/Los_Angeles": "Los Angeles",
    "America/Toronto": "Toronto",
    "America/Sao_Paulo": "São Paulo",
    "America/Mexico_City": "Mexico City",
    "Europe/London": "London",
    "Europe/Paris": "Paris",
    "Europe/Berlin": "Berlin",
    "Europe/Rome": "Rome",
    "Europe/Madrid": "Madrid",
    "Europe/Amsterdam": "Amsterdam",
    "Europe/Zurich": "Zurich",
    "Europe/Stockholm": "Stockholm",
    "Europe/Moscow": "Moscow",
    "Asia/Tokyo": "Tokyo",
    "Asia/Shanghai": "Shanghai",
    "Asia/Hong_Kong": "Hong Kong",
    "Asia/Singapore": "Singapore",
    "Asia/Kolkata": "Mumbai",
    "Asia/Calcutta": "Kolkata", // Handle both variants
    "Asia/Dubai": "Dubai",
    "Asia/Seoul": "Seoul",
    "Asia/Bangkok": "Bangkok",
    "Australia/Sydney": "Sydney",
    "Australia/Melbourne": "Melbourne",
    "Pacific/Auckland": "Auckland",
  };

  if (cityMap[timezone]) {
    return cityMap[timezone];
  }

  // Fallback: extract city name from timezone string
  const parts = timezone.split("/");
  if (parts.length >= 2) {
    return parts[parts.length - 1].replace(/_/g, " ");
  }

  return timezone;
};

/**
 * Get current browser timezone info
 */
export const getCurrentBrowserTimezone = (): TimezoneInfo => {
  const timezone = Intl.DateTimeFormat().resolvedOptions().timeZone;
  return getTimezoneInfo(timezone);
};

/**
 * Get popular timezones list with offsets using moment-timezone
 */
export const getPopularTimezones = (): TimezoneInfo[] => {
  // Popular timezones that users commonly need
  const popularTimezones = [
    "UTC",
    "America/New_York",
    "America/Chicago",
    "America/Denver",
    "America/Los_Angeles",
    "America/Toronto",
    "America/Sao_Paulo",
    "America/Mexico_City",
    "Europe/London",
    "Europe/Paris",
    "Europe/Berlin",
    "Europe/Rome",
    "Europe/Madrid",
    "Europe/Amsterdam",
    "Europe/Zurich",
    "Europe/Stockholm",
    "Europe/Moscow",
    "Asia/Tokyo",
    "Asia/Shanghai",
    "Asia/Hong_Kong",
    "Asia/Singapore",
    "Asia/Kolkata",
    "Asia/Dubai",
    "Asia/Seoul",
    "Asia/Bangkok",
    "Australia/Sydney",
    "Australia/Melbourne",
    "Pacific/Auckland",
  ];

  return popularTimezones.map(getTimezoneInfo).sort((a, b) => {
    // Sort by offset first, then by label
    const offsetA = parseFloat(a.offset.replace(":", "."));
    const offsetB = parseFloat(b.offset.replace(":", "."));
    if (offsetA !== offsetB) {
      return offsetA - offsetB;
    }
    return a.label.localeCompare(b.label);
  });
};

/**
 * Get ALL available timezones using moment-timezone
 */
export const getAllTimezones = (): TimezoneInfo[] => {
  return moment.tz
    .names()
    .map(getTimezoneInfo)
    .sort((a, b) => {
      // Sort by offset first, then by label
      const offsetA = parseFloat(a.offset.replace(":", "."));
      const offsetB = parseFloat(b.offset.replace(":", "."));
      if (offsetA !== offsetB) {
        return offsetA - offsetB;
      }
      return a.label.localeCompare(b.label);
    });
};

/**
 * Get timezone list (defaults to popular, but can get all)
 */
export const getTimezoneList = (
  includeAll: boolean = false,
): TimezoneInfo[] => {
  return includeAll ? getAllTimezones() : getPopularTimezones();
};

/**
 * Format timezone for display in settings - cleaner UX
 */
export const formatTimezoneDisplay = (
  timezone: string | null | undefined,
): string => {
  if (!timezone) {
    const browserTz = getCurrentBrowserTimezone();
    return `${browserTz.label} (UTC${browserTz.offset})`;
  }

  const tzInfo = getTimezoneInfo(timezone);
  return `${tzInfo.label} (UTC${tzInfo.offset})`;
};

/**
 * Get simple current time info for display
 */
export const getCurrentTimezoneInfo = () => {
  const browserTz = getCurrentBrowserTimezone();
  return {
    timezone: browserTz.label,
    timeString: browserTz.currentTime,
    offset: browserTz.offset,
  };
};
