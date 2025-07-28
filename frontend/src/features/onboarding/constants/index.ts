import { ProfessionOption, Question } from "../types";

export const professionOptions: ProfessionOption[] = [
  { label: "Student", value: "student" },
  { label: "Teacher", value: "teacher" },
  { label: "Engineer", value: "engineer" },
  { label: "Developer", value: "developer" },
  { label: "Designer", value: "designer" },
  { label: "Manager", value: "manager" },
  { label: "Consultant", value: "consultant" },
  { label: "Entrepreneur", value: "entrepreneur" },
  { label: "Researcher", value: "researcher" },
  { label: "Writer", value: "writer" },
  { label: "Artist", value: "artist" },
  { label: "Doctor", value: "doctor" },
  { label: "Lawyer", value: "lawyer" },
  { label: "Accountant", value: "accountant" },
  { label: "Sales", value: "sales" },
  { label: "Marketing", value: "marketing" },
  { label: "Analyst", value: "analyst" },
  { label: "Freelancer", value: "freelancer" },
  { label: "Retired", value: "retired" },
  { label: "Other", value: "other" },
];

export const FIELD_NAMES = {
  NAME: "name",
  // COUNTRY: "country",
  PROFESSION: "profession",
  RESPONSE_STYLE: "responseStyle",
  INSTRUCTIONS: "instructions",
} as const;

export const questions: Question[] = [
  {
    id: "1",
    question:
      "Hi there! I'm GAIA, your personal AI assistant. What should I call you?",
    placeholder: "Enter your name...",
    fieldName: FIELD_NAMES.NAME,
  },
  // {
  //   id: "2",
  //   question:
  //     "What country are you based in? This helps me understand your preferences better.",
  //   placeholder: "e.g., India, USA, Germany...",
  //   fieldName: FIELD_NAMES.COUNTRY,
  // },
  {
    id: "2",
    question: "What's your profession or main area of focus?",
    placeholder: "e.g., Software Developer, Student, Designer...",
    fieldName: FIELD_NAMES.PROFESSION,
  },
  {
    id: "3",
    question:
      "How would you prefer me to communicate with you? Choose your preferred response style:",
    placeholder: "Select your preferred communication style...",
    fieldName: FIELD_NAMES.RESPONSE_STYLE,
    chipOptions: [
      { label: "Brief", value: "brief" },
      { label: "Detailed", value: "detailed" },
      { label: "Casual", value: "casual" },
      { label: "Professional", value: "professional" },
      { label: "Skip this question", value: "skip" },
    ],
  },
  {
    id: "4",
    question: "Any specific instructions for how I should assist you?",
    placeholder: "Tell me anything specific you'd like me to know...",
    fieldName: FIELD_NAMES.INSTRUCTIONS,
    chipOptions: [{ label: "Skip this question", value: "skip" }],
  },
];
