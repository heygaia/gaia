/**
 * Profession-keyed message scripts for the platform preview shown in the
 * `platformPick` onboarding stage. One script set per profession value from
 * question one (the same value the wizard stores), three scripts each, one per
 * platform. Every script demonstrates the three things the copy promises:
 * morning briefings, urgent email flags, and workflow-finished pings, and
 * GAIA addresses the user by first name where the account has one.
 *
 * Rewrite scripts here; the preview component is data-driven and has no
 * other coupling to profession.
 */

import type {
  PlatformPreviewPlatform,
  PlatformScript,
  UserIdentity,
} from "./platformPreviewMessages.types";

export type {
  PlatformPreviewPlatform,
  PlatformScript,
  UserIdentity,
} from "./platformPreviewMessages.types";

type PlatformScripts = Record<PlatformPreviewPlatform, PlatformScript>;

export const PLATFORM_PREVIEW_ORDER: PlatformPreviewPlatform[] = [
  "telegram",
  "whatsapp",
  "imessage",
];

export const PLATFORM_LABELS: Record<PlatformPreviewPlatform, string> = {
  telegram: "Telegram",
  whatsapp: "WhatsApp",
  imessage: "iMessage",
};

export const PLATFORM_ICONS: Record<PlatformPreviewPlatform, string> = {
  telegram: "/images/icons/macos/telegram.webp",
  whatsapp: "/images/icons/macos/whatsapp.webp",
  imessage: "/images/icons/macos/imessage.webp",
};

/** The `professionOptions` values; a typed-in job falls back to `other`. */
export const PROFESSION_SCRIPT_KEYS = [
  "founder",
  "executive",
  "sales",
  "product",
  "creative",
  "engineering",
  "marketing",
  "finance",
  "student",
  "other",
] as const;
export type ProfessionScriptKey = (typeof PROFESSION_SCRIPT_KEYS)[number];

/** GAIA's lines carry this token; it always follows a word, so dropping it for
 *  an account with no first name leaves a natural sentence behind. */
const NAME_TOKEN = "{name}";

export function isPreviewPlatform(
  platform: string,
): platform is PlatformPreviewPlatform {
  return PLATFORM_PREVIEW_ORDER.includes(platform as PlatformPreviewPlatform);
}

function toScriptKey(profession: string | undefined): ProfessionScriptKey {
  return PROFESSION_SCRIPT_KEYS.includes(profession as ProfessionScriptKey)
    ? (profession as ProfessionScriptKey)
    : "other";
}

function personalize(text: string, firstName: string | undefined): string {
  return firstName
    ? text.replaceAll(NAME_TOKEN, firstName)
    : text.replaceAll(` ${NAME_TOKEN}`, "");
}

const FOUNDER_SCRIPTS: PlatformScripts = {
  telegram: {
    title: "GAIA",
    messages: [
      {
        from: "them",
        text: "morning {name}! inbox is sorted, 3 investor replies drafted and waiting for your ok.",
        time: "8:12",
      },
      {
        from: "them",
        text: "also the board deck is due friday. i pulled last month's numbers into the template already.",
        time: "8:12",
      },
      {
        from: "me",
        text: "anything from the seed lead?",
        time: "8:14",
        status: "read",
      },
      {
        from: "them",
        text: "yep, she asked for the updated runway. i attached it to the draft, just hit send.",
        time: "8:14",
      },
    ],
    subtitle: "bot",
  },
  whatsapp: {
    title: "GAIA",
    messages: [
      {
        from: "them",
        text: "Heads up {name}, your 2pm with the hiring candidate moved to 3. I updated the invite.",
        time: "9:05",
      },
      {
        from: "them",
        text: "Two team standups have no notes yet. Want me to chase?",
        time: "9:05",
      },
      {
        from: "me",
        text: "chase them, and remind me to send the offer letter",
        time: "9:07",
        status: "read",
      },
      {
        from: "them",
        text: "Done. Both pinged, and I'll remind you at 4 about the offer.",
        time: "9:07",
      },
    ],
  },
  imessage: {
    title: "GAIA",
    messages: [
      {
        from: "them",
        text: "Morning {name}. Runway update is ready, MRR is up 6% on last month.",
        time: "7:48",
      },
      {
        from: "them",
        text: "Your competitor shipped pricing changes overnight. One-paragraph summary is in your inbox.",
        time: "7:48",
      },
      {
        from: "me",
        text: "book 20 min with Priya to go over it",
        time: "7:51",
        status: "read",
      },
      {
        from: "them",
        text: "Booked for 11:30. She has the summary too.",
        time: "7:51",
      },
    ],
  },
};

const EXECUTIVE_SCRIPTS: PlatformScripts = {
  telegram: {
    title: "GAIA",
    messages: [
      {
        from: "them",
        text: "morning {name}! 3 reports landed overnight, i read them so you don't have to. one decision needs you.",
        time: "7:55",
      },
      {
        from: "them",
        text: "ops wants a yes or no on the vendor contract by noon. the two options are in your inbox, side by side.",
        time: "7:55",
      },
      {
        from: "me",
        text: "go with option B, tell them",
        time: "7:58",
        status: "read",
      },
      {
        from: "them",
        text: "sent {name}. contract's on its way for signature.",
        time: "7:58",
      },
    ],
    subtitle: "bot",
  },
  whatsapp: {
    title: "GAIA",
    messages: [
      {
        from: "them",
        text: "Heads up {name}, the board pre-read got 4 comments. I summarised them, two are quick fixes.",
        time: "8:20",
      },
      {
        from: "them",
        text: "Your 10am and 10:30 overlap. Move the 10:30?",
        time: "8:20",
      },
      {
        from: "me",
        text: "yes, and draft a reply to the CFO's comment",
        time: "8:22",
        status: "read",
      },
      {
        from: "them",
        text: "Moved to 11. Draft's in your inbox, tone matches your last reply to him.",
        time: "8:22",
      },
    ],
  },
  imessage: {
    title: "GAIA",
    messages: [
      {
        from: "them",
        text: "Morning {name}. Today: leadership sync at 9, two 1:1s, investor dinner at 7.",
        time: "7:30",
      },
      {
        from: "them",
        text: "The Q3 numbers you asked for are in the sync invite. Revenue beat plan by 4%.",
        time: "7:30",
      },
      {
        from: "me",
        text: "cancel the 3pm, I need thinking time",
        time: "7:33",
        status: "read",
      },
      {
        from: "them",
        text: "Cancelled and rescheduled for Thursday. Your afternoon is clear.",
        time: "7:33",
      },
    ],
  },
};

const SALES_SCRIPTS: PlatformScripts = {
  telegram: {
    title: "GAIA",
    messages: [
      {
        from: "them",
        text: "morning {name}! 2 leads went quiet this week. i drafted follow-ups for both, warm not pushy.",
        time: "8:05",
      },
      {
        from: "them",
        text: "your 11am call is with Nadia at Northwind. she just raised a series A, i put the details in your brief.",
        time: "8:05",
      },
      {
        from: "me",
        text: "send both follow-ups",
        time: "8:07",
        status: "read",
      },
      {
        from: "them",
        text: "sent. i'll flag you the second either one replies.",
        time: "8:07",
      },
    ],
    subtitle: "bot",
  },
  whatsapp: {
    title: "GAIA",
    messages: [
      {
        from: "them",
        text: "Heads up {name}, the Acme proposal was opened 3 times last night. They're reading it.",
        time: "9:10",
      },
      {
        from: "them",
        text: "Their CTO also joined the deal thread. I pulled his background into your call notes.",
        time: "9:10",
      },
      {
        from: "me",
        text: "book a demo with them for tomorrow",
        time: "9:12",
        status: "read",
      },
      {
        from: "them",
        text: "Sent them three slots. I'll confirm the moment they pick one.",
        time: "9:12",
      },
    ],
  },
  imessage: {
    title: "GAIA",
    messages: [
      {
        from: "them",
        text: "Morning {name}. Pipeline is at 82% of quota, two deals could close this week.",
        time: "7:45",
      },
      {
        from: "them",
        text: "Call research is done for all 4 meetings today. Each brief is one screen.",
        time: "7:45",
      },
      {
        from: "me",
        text: "move the Lumen call to after lunch",
        time: "7:48",
        status: "read",
      },
      {
        from: "them",
        text: "Moved to 2:15. Their side accepted already.",
        time: "7:48",
      },
    ],
  },
};

const PRODUCT_SCRIPTS: PlatformScripts = {
  telegram: {
    title: "GAIA",
    messages: [
      {
        from: "them",
        text: "morning {name}! 14 pieces of feedback came in overnight. 3 are the same onboarding bug, i grouped them.",
        time: "8:20",
      },
      {
        from: "them",
        text: "the spec for the export feature is drafted from your notes. it's in the doc, needs your eyes on scope.",
        time: "8:20",
      },
      {
        from: "me",
        text: "file the onboarding bug and tag it high",
        time: "8:22",
        status: "read",
      },
      {
        from: "them",
        text: "filed and tagged. eng lead is on it, i'll tell you when it ships.",
        time: "8:22",
      },
    ],
    subtitle: "bot",
  },
  whatsapp: {
    title: "GAIA",
    messages: [
      {
        from: "them",
        text: "Heads up {name}, design posted the new checkout flow. Two comments from support are worth a look.",
        time: "9:00",
      },
      {
        from: "them",
        text: "Your roadmap review is at 2, I put the updated numbers in the invite.",
        time: "9:00",
      },
      {
        from: "me",
        text: "summarise the support comments for the review",
        time: "9:03",
        status: "read",
      },
      {
        from: "them",
        text: "Done, one paragraph each, added to the invite.",
        time: "9:03",
      },
    ],
  },
  imessage: {
    title: "GAIA",
    messages: [
      {
        from: "them",
        text: "Morning {name}. Feature adoption is up 12% since the release. Three users asked for the same thing.",
        time: "7:50",
      },
      {
        from: "them",
        text: "Your customer interview is at 11. I wrote the questions from last week's gaps.",
        time: "7:50",
      },
      {
        from: "me",
        text: "send the questions to Dev before the call",
        time: "7:53",
        status: "read",
      },
      {
        from: "them",
        text: "Sent. He's reviewed them and added one.",
        time: "7:53",
      },
    ],
  },
};

const CREATIVE_SCRIPTS: PlatformScripts = {
  telegram: {
    title: "GAIA",
    messages: [
      {
        from: "them",
        text: "morning {name}! 2 clients replied on the brand deck. one loves it, one wants the type bigger.",
        time: "8:30",
      },
      {
        from: "them",
        text: "your client call moved to 3. that gives you the whole morning to make.",
        time: "8:30",
      },
      {
        from: "me",
        text: "send the type feedback to the print shop",
        time: "8:32",
        status: "read",
      },
      {
        from: "them",
        text: "sent {name}. they'll have a proof by tomorrow.",
        time: "8:32",
      },
    ],
    subtitle: "bot",
  },
  whatsapp: {
    title: "GAIA",
    messages: [
      {
        from: "them",
        text: "Heads up {name}, the invoice from March finally got paid. I logged it.",
        time: "9:15",
      },
      {
        from: "them",
        text: "New inquiry came in, a podcast wants cover art. Budget looks right for you.",
        time: "9:15",
      },
      {
        from: "me",
        text: "reply that I can start next week",
        time: "9:17",
        status: "read",
      },
      {
        from: "them",
        text: "Replied, with your usual rate and next Tuesday as the start.",
        time: "9:17",
      },
    ],
  },
  imessage: {
    title: "GAIA",
    messages: [
      {
        from: "them",
        text: "Morning {name}. Your portfolio got 40 new visits from that post yesterday.",
        time: "7:55",
      },
      {
        from: "them",
        text: "Two references you saved this week are in a folder called moodboard, ready for the pitch.",
        time: "7:55",
      },
      {
        from: "me",
        text: "block tomorrow morning for deep work",
        time: "7:58",
        status: "read",
      },
      {
        from: "them",
        text: "Blocked 9 to 1. No meetings can land there now.",
        time: "7:58",
      },
    ],
  },
};

const ENGINEERING_SCRIPTS: PlatformScripts = {
  telegram: {
    title: "GAIA",
    messages: [
      {
        from: "them",
        text: "morning {name}! pushed your 9am standup back to 10 so you've got a bit more breathing room.",
        time: "8:40",
      },
      {
        from: "them",
        text: "2 code reviews are waiting on you, and last night's deploy went through fine.",
        time: "8:40",
      },
      {
        from: "me",
        text: "anything actually on fire?",
        time: "8:41",
        status: "read",
      },
      {
        from: "them",
        text: "nope, all quiet. go grab your coffee first.",
        time: "8:41",
      },
    ],
    subtitle: "bot",
  },
  whatsapp: {
    title: "GAIA",
    messages: [
      {
        from: "them",
        text: "Heads up {name}, your tech lead replied on the migration thread. She wants a call today.",
        time: "9:05",
      },
      {
        from: "them",
        text: "The flaky test you muted is failing on main again. I opened an issue with the last 3 runs.",
        time: "9:05",
      },
      {
        from: "me",
        text: "book 15 min with her after lunch",
        time: "9:07",
        status: "read",
      },
      {
        from: "them",
        text: "Booked 1:30. The thread and the issue are in the invite.",
        time: "9:07",
      },
    ],
  },
  imessage: {
    title: "GAIA",
    messages: [
      {
        from: "them",
        text: "Morning {name}. The deploy you kicked off last night finished clean, zero errors.",
        time: "7:52",
      },
      {
        from: "them",
        text: "Two PRs are waiting on your review. I summarised both, the second one touches auth.",
        time: "7:52",
      },
      {
        from: "me",
        text: "move standup to 10, I want to read the auth one first",
        time: "7:55",
        status: "read",
      },
      {
        from: "them",
        text: "Done. Standup is at 10, the team has the new invite.",
        time: "7:55",
      },
    ],
  },
};

const MARKETING_SCRIPTS: PlatformScripts = {
  telegram: {
    title: "GAIA",
    messages: [
      {
        from: "them",
        text: "morning {name}! yesterday's campaign email got a 31% open rate, best this quarter.",
        time: "8:15",
      },
      {
        from: "them",
        text: "3 people replied asking about pricing. i drafted replies and looped in sales on one.",
        time: "8:15",
      },
      {
        from: "me",
        text: "what's the plan for the launch post?",
        time: "8:17",
        status: "read",
      },
      {
        from: "them",
        text: "draft's ready, i pulled the 3 strongest customer quotes in. want it in your inbox?",
        time: "8:17",
      },
    ],
    subtitle: "bot",
  },
  whatsapp: {
    title: "GAIA",
    messages: [
      {
        from: "them",
        text: "Heads up {name}, the agency sent the new landing page copy. Two headlines to pick from.",
        time: "9:20",
      },
      {
        from: "them",
        text: "Your content review moved to 4. Everything for it is in the invite.",
        time: "9:20",
      },
      {
        from: "me",
        text: "go with the second headline",
        time: "9:22",
        status: "read",
      },
      {
        from: "them",
        text: "Told them. They'll have the page live by Thursday.",
        time: "9:22",
      },
    ],
  },
  imessage: {
    title: "GAIA",
    messages: [
      {
        from: "them",
        text: "Morning {name}. Weekly numbers are in: traffic up 9%, signups flat, one post did most of the work.",
        time: "7:40",
      },
      {
        from: "them",
        text: "A journalist asked for a quote by noon. I drafted one in your voice.",
        time: "7:40",
      },
      {
        from: "me",
        text: "send the quote, and schedule the recap post for 10",
        time: "7:43",
        status: "read",
      },
      {
        from: "them",
        text: "Quote sent, recap scheduled for 10. I'll share the reach at 5.",
        time: "7:43",
      },
    ],
  },
};

const FINANCE_SCRIPTS: PlatformScripts = {
  telegram: {
    title: "GAIA",
    messages: [
      {
        from: "them",
        text: "morning {name}! month-end close is 80% there. 4 invoices are still missing receipts, i chased all four.",
        time: "8:00",
      },
      {
        from: "them",
        text: "the FX move overnight shifts the forecast by about 2%. updated sheet is in your inbox.",
        time: "8:00",
      },
      {
        from: "me",
        text: "which invoices?",
        time: "8:02",
        status: "read",
      },
      {
        from: "them",
        text: "two from travel, two from the design agency. i'll ping you when they land.",
        time: "8:02",
      },
    ],
    subtitle: "bot",
  },
  whatsapp: {
    title: "GAIA",
    messages: [
      {
        from: "them",
        text: "Heads up {name}, the auditor asked for the Q2 reconciliation. I found it and replied with the file.",
        time: "9:30",
      },
      {
        from: "them",
        text: "Your budget review is at 2. Variance summary is in the invite, two lines need a comment.",
        time: "9:30",
      },
      {
        from: "me",
        text: "draft the comments from last month's notes",
        time: "9:32",
        status: "read",
      },
      {
        from: "them",
        text: "Drafted both, they're in the sheet next to the numbers.",
        time: "9:32",
      },
    ],
  },
  imessage: {
    title: "GAIA",
    messages: [
      {
        from: "them",
        text: "Morning {name}. Cash position is steady, runway is 19 months on current burn.",
        time: "7:35",
      },
      {
        from: "them",
        text: "Payroll is queued for Friday. One new starter is missing bank details, I've asked HR.",
        time: "7:35",
      },
      {
        from: "me",
        text: "remind me to approve payroll thursday morning",
        time: "7:38",
        status: "read",
      },
      {
        from: "them",
        text: "Set for Thursday 9am. I'll include the final total.",
        time: "7:38",
      },
    ],
  },
};

const STUDENT_SCRIPTS: PlatformScripts = {
  telegram: {
    title: "GAIA",
    messages: [
      {
        from: "them",
        text: "morning {name}! your essay draft is due thursday. i pulled the 5 sources you saved into one outline.",
        time: "8:25",
      },
      {
        from: "them",
        text: "lecture at 10 moved rooms, it's in the science block now. calendar's updated.",
        time: "8:25",
      },
      {
        from: "me",
        text: "what's due this week?",
        time: "8:27",
        status: "read",
      },
      {
        from: "them",
        text: "essay thursday, problem set friday. i blocked 2 hours tomorrow for the problem set.",
        time: "8:27",
      },
    ],
    subtitle: "bot",
  },
  whatsapp: {
    title: "GAIA",
    messages: [
      {
        from: "them",
        text: "Heads up {name}, your professor replied about the extension. Yes, until Monday.",
        time: "9:40",
      },
      {
        from: "them",
        text: "Your group chat picked Wednesday 6pm for the project. I added it to your calendar.",
        time: "9:40",
      },
      {
        from: "me",
        text: "remind me to email the internship people tonight",
        time: "9:42",
        status: "read",
      },
      {
        from: "them",
        text: "Reminder set for 8pm, with the draft you wrote last week attached.",
        time: "9:42",
      },
    ],
  },
  imessage: {
    title: "GAIA",
    messages: [
      {
        from: "them",
        text: "Morning {name}. Three lectures today, one quiz at 2. Your notes from last week are summarised.",
        time: "7:45",
      },
      {
        from: "them",
        text: "The library book you need is available again. Want me to reserve it?",
        time: "7:45",
      },
      {
        from: "me",
        text: "yes, and block friday afternoon to study",
        time: "7:48",
        status: "read",
      },
      {
        from: "them",
        text: "Reserved, and Friday 1 to 5 is blocked. No one can book over it.",
        time: "7:48",
      },
    ],
  },
};

const OTHER_SCRIPTS: PlatformScripts = {
  telegram: {
    title: "GAIA",
    messages: [
      {
        from: "them",
        text: "morning {name}! inbox is sorted, 2 emails need a reply from you and i drafted both.",
        time: "8:15",
      },
      {
        from: "them",
        text: "dentist at 11, call with Sam at 3. Sam wants the proposal first, it's attached to the invite.",
        time: "8:15",
      },
      {
        from: "me",
        text: "send the proposal now",
        time: "8:17",
        status: "read",
      },
      {
        from: "them",
        text: "sent. i'll nudge you before the call.",
        time: "8:17",
      },
    ],
    subtitle: "bot",
  },
  whatsapp: {
    title: "GAIA",
    messages: [
      {
        from: "them",
        text: "Heads up {name}, your 3pm moved to 4. I updated the invite and told Sam.",
        time: "9:25",
      },
      {
        from: "them",
        text: "The form you were waiting on came back signed. It's filed.",
        time: "9:25",
      },
      {
        from: "me",
        text: "remind me to call the bank tomorrow",
        time: "9:27",
        status: "read",
      },
      {
        from: "them",
        text: "Reminder set for 10am tomorrow, with the account number in it.",
        time: "9:27",
      },
    ],
  },
  imessage: {
    title: "GAIA",
    messages: [
      {
        from: "them",
        text: "Morning {name}. Two things need you today, the rest I handled.",
        time: "7:50",
      },
      {
        from: "them",
        text: "Your package arrives between 2 and 4. I'll ping you when it's at the door.",
        time: "7:50",
      },
      {
        from: "me",
        text: "move my 2pm so I'm home for it",
        time: "7:53",
        status: "read",
      },
      {
        from: "them",
        text: "Moved to 11. You're free from 2.",
        time: "7:53",
      },
    ],
  },
};

const PROFESSION_SCRIPTS: Record<ProfessionScriptKey, PlatformScripts> = {
  founder: FOUNDER_SCRIPTS,
  executive: EXECUTIVE_SCRIPTS,
  sales: SALES_SCRIPTS,
  product: PRODUCT_SCRIPTS,
  creative: CREATIVE_SCRIPTS,
  engineering: ENGINEERING_SCRIPTS,
  marketing: MARKETING_SCRIPTS,
  finance: FINANCE_SCRIPTS,
  student: STUDENT_SCRIPTS,
  other: OTHER_SCRIPTS,
};

export function getPlatformScript(
  profession: string | undefined,
  platform: PlatformPreviewPlatform,
  user: UserIdentity = { firstName: undefined },
): PlatformScript {
  const raw = PROFESSION_SCRIPTS[toScriptKey(profession)][platform];
  return {
    ...raw,
    messages: raw.messages.map((m) =>
      m.from === "them" && m.text
        ? { ...m, text: personalize(m.text, user.firstName) }
        : m,
    ),
  };
}
