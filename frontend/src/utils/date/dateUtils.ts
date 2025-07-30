import { isValid, parseISO } from "date-fns";


const nth = (date: number): string => {
  if (date > 3 && date < 21) return "th";
  switch (date % 10) {
    case 1:
      return "st";
    case 2:
      return "nd";
    case 3:
      return "rd";
    default:
      return "th";
  }
};

export default function fetchDate(): string {
  return new Date().toISOString();
}

export const parsingDate = (isoString: string) => {
  const withoutTimezone = isoString.replace(/([+-]\d{2}:\d{2})$/, "");
  const date = new Date(withoutTimezone);
  return new Intl.DateTimeFormat("en-US", {
    year: "numeric",
    month: "long",
    day: "numeric",
    hour: "numeric",
    minute: "numeric",
    hour12: true,
  }).format(date);
};

export function parseDate(isoDateString: string): string {
  const date = new Date(isoDateString);
  const optionsTime: Intl.DateTimeFormatOptions = {
    hour: "numeric",
    minute: "2-digit",
    hour12: true,
  };
  const optionsMonth: Intl.DateTimeFormatOptions = { month: "short" };
  const optionsYear: Intl.DateTimeFormatOptions = { year: "2-digit" };

  const time = date
    .toLocaleString(navigator.language, optionsTime)
    .toUpperCase();
  const month = date.toLocaleString(navigator.language, optionsMonth);
  const year = date.toLocaleString(navigator.language, optionsYear);
  const day = date.getDate();

  return `${time} ${day}${nth(day)} ${month} '${year}`.trim();
}

export function parseDate2(isoDateString: string): string {
  const date = new Date(isoDateString);
  const optionsMonth: Intl.DateTimeFormatOptions = { month: "short" };
  const month = date.toLocaleString(navigator.language, optionsMonth);
  const day = date.getDate();

  return `${day}${nth(day)} ${month}`.trim();
}


/**
 * Formats a date string into a human-readable date format
 * Examples: "June 10, 2025", "March 15, 2024", "December 1, 2023"
 *
 * @param dateString - Date string in ISO format (YYYY-MM-DD) or any valid date format
 * @returns Human-readable date string
 */
export function formatRelativeDate(dateString: string): string {
  try {
    // Try to parse the date string
    let date: Date;

    // If it's in YYYY-MM-DD format, parse it as ISO
    if (/^\d{4}-\d{2}-\d{2}$/.test(dateString)) {
      date = parseISO(dateString);
    } else {
      // Try parsing as a regular date string
      date = new Date(dateString);
    }

    // Check if the date is valid
    if (!isValid(date)) {
      console.warn(`Invalid date string: ${dateString}`);
      return dateString; // Return original string if parsing fails
    }

    // Format as readable date
    return date.toLocaleDateString("en-US", {
      year: "numeric",
      month: "long",
      day: "numeric",
    });
  } catch (error) {
    console.warn(`Error formatting date: ${dateString}`, error);
    return dateString; // Return original string if error occurs
  }
}
