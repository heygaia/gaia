// greetingUtils.ts - Utility functions for time-based greetings

/**
 * Get a conversational greeting message based on the current time of day
 * @returns A greeting string appropriate for the current time with assistant-like personality
 */
export const getTimeBasedGreeting = (): string => {
  const currentHour = new Date().getHours();

  const morningGreetings = [
    "What's brewing today?",
    "Rise and conquer!",
    "Today's mission?",
    "Morning, champion!",
    "Let's make magic happen",
    "Fresh day, fresh possibilities",
    "What adventure awaits?",
    "Time to shine bright",
    "Ready to crush it?",
    "New day, new wins",
    "Morning energy activated",
    "What's the game plan?",
    "Sunrise = fresh start",
    "Let's build something cool",
  ];

  const afternoonGreetings = [
    "Afternoon check-in. What’s next?",
    "Back at it. Keep pushing.",
    "Midday momentum, let’s move.",
    "How’s the grind going?",
    "Push through the slump.",
    "Let’s close some loops.",
    "Keep stacking wins.",
    "Any progress updates?",
    "Execution mode: ON.",
    "Time to refocus.",
    "Dial it back in.",
    "Momentum compounds.",
    "Still building strong?",
    "Halfway there, keep going.",
    "Let’s lock in the second half.",
  ];

  const eveningGreetings = [
    "Evening grind—what’s left?",
    "Day’s endgame. One last push?",
    "Time to finish strong.",
    "Evening hustle check.",
    "Closing hours = clutch hours.",
    "Strong finish > strong start.",
    "Any loose ends to wrap?",
    "End the day on your terms.",
    "Final sprint of the day.",
    "Keep it sharp till the end.",
    "What’s tonight’s plan?",
    "Last task before rest?",
    "Push through, then recharge.",
    "Evening clarity unlocked.",
    "Let’s seal today’s wins.",
  ];

  const nightGreetings = [
    "Late hours, clear thoughts.",
    "What’s the midnight mission?",
    "Silence fuels creativity.",
    "Night grind = no distractions.",
    "Moonlight mode: ON.",
    "Ideas flow better after dark.",
    "Still cooking something?",
    "Midnight clarity unlocked.",
    "Night shift in progress.",
    "Who needs 9–5 anyway?",
    "Dark hours, bright ideas.",
    "World’s quiet, your turn.",
    "Night = deep work zone.",
    "Late night energy unlocked.",
    "Tomorrow prep starts now.",
  ];

  let greetings: string[];
  if (currentHour >= 5 && currentHour < 12) {
    greetings = morningGreetings;
  } else if (currentHour >= 12 && currentHour < 17) {
    greetings = afternoonGreetings;
  } else if (currentHour >= 17 && currentHour < 21) {
    greetings = eveningGreetings;
  } else {
    greetings = nightGreetings;
  }

  const randomIndex = Math.floor(Math.random() * greetings.length);
  return greetings[randomIndex];
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
 * Get a complete time-based greeting
 * @param userName - Optional user's name for personalization
 * @returns A greeting string
 */
export const getCompleteTimeBasedGreeting = (userName?: string): string => {
  return getPersonalizedTimeBasedGreeting(userName);
};
