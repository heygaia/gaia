import type { NeedOption, ProfessionOption, Question } from "../types";

export const professionOptions: ProfessionOption[] = [
  { label: "Founder / CEO", value: "founder" },
  { label: "Executive", value: "executive" },
  { label: "Sales", value: "sales" },
  { label: "Product", value: "product" },
  { label: "Creative", value: "creative" },
  { label: "Engineering", value: "engineering" },
  { label: "Marketing", value: "marketing" },
  { label: "Finance", value: "finance" },
  { label: "Student", value: "student" },
  { label: "Other", value: "other" },
];

/**
 * Q2 options: jobs the user hands GAIA, each a different kind of work, so two
 * people rarely pick the same pair and the picks mean something downstream
 * (the seeded thread's chips, the connect-link order, the bot's opener).
 * `value` mirrors the backend `OnboardingNeed` StrEnum
 * (`apps/api/app/models/user_models.py`) one-for-one — the API rejects
 * anything outside that set, so the two lists must stay in lockstep. The
 * first-person phrasing lives in `first_message.py` next to the enum.
 */
export const needOptions: NeedOption[] = [
  { value: "inbox", label: "Answer my email" },
  { value: "calendar", label: "Run my calendar" },
  { value: "research", label: "Research and brief me" },
  { value: "followups", label: "Chase my follow-ups" },
  { value: "automation", label: "Do my recurring chores" },
];

export function isKnownNeed(value: string): boolean {
  return needOptions.some((option) => option.value === value);
}

/** The catch-all chip; picking it opens a free-text field whose value replaces
 * this marker as the draft. Anything not in `professionOptions` is a typed job. */
export const OTHER_PROFESSION = "other";

export function isListedProfession(value: string): boolean {
  return (
    value !== OTHER_PROFESSION &&
    professionOptions.some((option) => option.value === value)
  );
}

/** Q2's catch-all. Not a backend need: it opens a field whose text is sent as
 * `other_need`, so this value never lands in `selectedNeeds`. */
export const OTHER_NEED = "something_else";
export const OTHER_NEED_OPTION: NeedOption = {
  value: OTHER_NEED,
  label: "Something else",
};

export const NEEDS_MIN_SELECTION = 1;
/** Mirrors `NEEDS_MAX_SELECTION` in apps/api user_models.py: the API 422s a
 * third need. "Something else" counts as a pick, so the field closes the grid. */
export const NEEDS_MAX_SELECTION = 2;

/** Mirror `OnboardingPreferences` in apps/api user_models.py: the profession
 * validator caps at 80 and `OTHER_NEED_MAX_LENGTH` at 120; longer text 422s.
 * 80, not 50, because Q1 asks "What do you do?" and people answer in a
 * sentence — "I'm a founder and designer building a startup" is already 46. */
export const PROFESSION_MAX_LENGTH = 80;
export const OTHER_NEED_MAX_LENGTH = 120;

/** Query key Dodo's return URL carries back into the wizard after checkout.
 * Mirrors ONBOARDING_CHECKOUT_RETURN_PATH in apps/api payment_models.py. */
export const CHECKOUT_RETURNED_PARAM = "checkout";

export const FIELD_NAMES = {
  PROFESSION: "profession",
  NEEDS: "needs",
} as const;

/** "Founder, got it." for a listed job; a typed or skipped one gets a plain ack. */
function professionAck(responses: Record<string, string>): string {
  const picked = responses[FIELD_NAMES.PROFESSION];
  const listed = picked && isListedProfession(picked);
  const label = listed
    ? professionOptions.find((option) => option.value === picked)?.label
    : undefined;
  return label ? `${label.split(" / ")[0]}, got it.` : "Got it.";
}

export const questions: Question[] = [
  {
    id: "1",
    lines: () => [
      "Hey! I'm GAIA. Nice to meet you.",
      "Think about everything you did yesterday. Email, calendar, meetings, sure, that's the obvious stuff.",
      "But also the research, the chasing people, the spreadsheet, the booking, that one thing you do every week and hate. I do all of that. Not you.",
      "So, what do you do for work?",
    ],
    fieldName: FIELD_NAMES.PROFESSION,
  },
  {
    id: "2",
    lines: (responses) => [
      professionAck(responses),
      "What do you want off your plate first? Pick up to two.",
    ],
    fieldName: FIELD_NAMES.NEEDS,
  },
];
