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
 * Q2 options everyone sees: pains in the user's words, each a different job
 * GAIA can start on, so the picks mean something downstream (the seeded
 * thread's chips, the connect-link order, the bot's opener).
 * `value` mirrors the backend `OnboardingNeed` StrEnum
 * (`apps/api/app/models/user_models.py`) one-for-one — the API rejects
 * anything outside that set, so the two lists must stay in lockstep. The
 * first-person phrasing lives in `first_message.py` next to the enum.
 */
export const needOptions: NeedOption[] = [
  { value: "inbox", label: "Inbox out of control" },
  { value: "calendar", label: "Walking into meetings cold" },
  { value: "mornings", label: "Mornings start behind" },
  { value: "reminders", label: "Things I keep forgetting" },
  { value: "grunt_work", label: "Grunt work every week" },
  { value: "tools", label: "Too many tools to juggle" },
];

/**
 * Two extra pains per Q1 role, shown first and marked as personalised. Keys
 * are `professionOptions` values; mirrors `ROLE_NEEDS` on the API, which
 * rejects a role need sent with a different profession.
 */
const roleNeedOptions: Record<string, NeedOption[]> = {
  founder: [
    { value: "founder_team_updates", label: "Team updates I chase" },
    { value: "founder_competitors", label: "Competitors I never track" },
  ],
  executive: [
    { value: "executive_reports", label: "Reports I never read" },
    { value: "executive_decisions", label: "Decisions piling up" },
  ],
  sales: [
    { value: "sales_leads", label: "Leads going cold" },
    { value: "sales_call_research", label: "Research before every call" },
  ],
  product: [
    { value: "product_feedback", label: "Feedback scattered everywhere" },
    { value: "product_specs", label: "Specs that take forever" },
  ],
  marketing: [
    { value: "marketing_content", label: "Content always behind" },
    { value: "marketing_reports", label: "Reports by hand" },
  ],
  engineering: [
    { value: "engineering_prs", label: "PRs waiting on me" },
    { value: "engineering_notifications", label: "Drowning in notifications" },
  ],
  finance: [
    { value: "finance_numbers", label: "Chasing people for numbers" },
    { value: "finance_reports", label: "Same report every week" },
  ],
  creative: [
    { value: "creative_revisions", label: "Client revisions piling up" },
    { value: "creative_deadlines", label: "Deadlines sneaking up" },
  ],
  student: [
    { value: "student_assignments", label: "Assignments piling up" },
    { value: "student_exams", label: "Exams I'm not ready for" },
  ],
};

/** How the role reads inside "Personalised for you, since you're …". */
export const ROLE_PHRASES: Record<string, string> = {
  founder: "a founder",
  executive: "an executive",
  sales: "in sales",
  product: "in product",
  creative: "a creative",
  engineering: "an engineer",
  marketing: "in marketing",
  finance: "in finance",
  student: "a student",
};

const allNeedOptions: NeedOption[] = [
  ...needOptions,
  ...Object.values(roleNeedOptions).flat(),
];

/** The Q2 grid for a Q1 answer: the role's two pains first, then the shared six. */
export function needOptionsFor(profession: string | null): NeedOption[] {
  const role = profession ? roleNeedOptions[profession] : undefined;
  return role ? [...role, ...needOptions] : needOptions;
}

export function isRoleNeed(value: string): boolean {
  return (
    !needOptions.some((option) => option.value === value) && isKnownNeed(value)
  );
}

export function isKnownNeed(value: string): boolean {
  return allNeedOptions.some((option) => option.value === value);
}

export function needLabel(value: string): string | undefined {
  return allNeedOptions.find((option) => option.value === value)?.label;
}

/** Under the Q2 grid: two picks set up the first thing, they are not a ceiling. */
export const NEEDS_HINT =
  "Just a starting point. You can hand me more anytime.";

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
