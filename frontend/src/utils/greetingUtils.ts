// greetingUtils.ts - Utility functions for time-based greetings

/**
 * Get a greeting message based on the current time of day
 * @returns A greeting string appropriate for the current time
 */
export const getTimeBasedGreeting = (): string => {
  const currentHour = new Date().getHours();

  if (currentHour >= 5 && currentHour < 12) {
    return "Good morning";
  } else if (currentHour >= 12 && currentHour < 17) {
    return "Good afternoon";
  } else if (currentHour >= 17 && currentHour < 21) {
    return "Good evening";
  } else {
    return "Good night";
  }
};

/**
 * Get a contextual follow-up message based on the time of day
 * @returns A contextual message that follows the greeting
 */
export const getTimeBasedContext = (): string => {
  const currentHour = new Date().getHours();

  if (currentHour >= 5 && currentHour < 12) {
    return "Ready to start your day?";
  } else if (currentHour >= 12 && currentHour < 17) {
    return "How's your day going?";
  } else if (currentHour >= 17 && currentHour < 21) {
    return "How was your day?";
  } else {
    return "Working late or having trouble sleeping?";
  }
};

/**
 * Get an emoji based on the time of day
 * @returns An emoji string appropriate for the current time
 */
export const getTimeBasedEmoji = (): string => {
  const currentHour = new Date().getHours();

  if (currentHour >= 5 && currentHour < 12) {
    return "☀️";
  } else if (currentHour >= 12 && currentHour < 17) {
    return "🌤️";
  } else if (currentHour >= 17 && currentHour < 21) {
    return "🌅";
  } else {
    return "🌙";
  }
};

/**
 * Get a personalized greeting message with user's name
 * @param userName - The user's name to include in the greeting
 * @returns A personalized greeting string
 */
export const getPersonalizedTimeBasedGreeting = (userName?: string): string => {
  const baseGreeting = getTimeBasedGreeting();

  if (!userName || userName.trim() === "") {
    return baseGreeting;
  }

  // Extract first name from full name
  const firstName = userName.split(" ")[0];
  return `${baseGreeting}, ${firstName}`;
};

/**
 * Get a complete time-based greeting with context
 * @param userName - Optional user's name for personalization
 * @returns An object containing greeting, context, and emoji
 */
export const getCompleteTimeBasedGreeting = (userName?: string) => {
  return {
    greeting: getPersonalizedTimeBasedGreeting(userName),
    context: getTimeBasedContext(),
    emoji: getTimeBasedEmoji(),
  };
};
