import { motion } from "framer-motion";
import {
  BedDouble,
  BookOpen,
  Briefcase,
  Clock,
  FlaskConical,
  GitBranch,
  Landmark,
  Plane,
  Presentation,
  Search,
  ShoppingCart,
  Target,
  Users,
} from "lucide-react";
import React from "react";

// --- TYPE DEFINITIONS ---

export interface SlideContent {
  title: string;
  subtitle?: string;
  points?: string[];
  image?: string;
  bgColor: string;
  textColor: string;
  highlightColor: string;
  fontClass?: string;
}

export interface DemoData {
  id: number;
  email: {
    subject: string;
    sender: string;
    senderEmail: string;
    body: (highlighted: boolean) => React.ReactNode;
    topic: string;
    dueDate: string;
  };
  calendar: {
    month: string;
    year: number;
    dayOfWeek: string;
    dueDay: number;
  };
  slides: SlideContent[];
  roadmap: {
    icon: React.ElementType;
    label: string;
    time: string;
  }[];
}

// --- DEMO CONTENT ---

export const demoContents: DemoData[] = [
  // --- DATASET 1: NEURAL NETWORKS (STUDENT) ---
  {
    id: 1,
    email: {
      subject: "CS401 Assignment: Neural Networks",
      sender: "Prof. Smith",
      senderEmail: "prof.smith@university.edu",
      topic: "Neural Networks and Deep Learning",
      dueDate: "August 15th, 11:59 PM",
      body: (highlighted: boolean) => (
        <>
          Hi team,
          <br />
          <br />
          Please research and prepare a comprehensive presentation on{" "}
          <span className="relative inline-block">
            <motion.span
              className="absolute inset-0 -mx-1 -my-0.5 rounded bg-yellow-200/80"
              initial={{ scaleX: 0, originX: 0 }}
              animate={highlighted ? { scaleX: 1 } : { scaleX: 0 }}
              transition={{ duration: 0.6, ease: [0.22, 1, 0.36, 1] }}
            />
            <span className="relative font-semibold text-gray-900">
              Neural Networks and Deep Learning
            </span>
          </span>
          . Include practical applications and recent developments.
          <br />
          <br />
          This will be a major part of your grade.
          <br />
          <br />
          <span className="relative inline-flex items-center gap-2">
            <Clock className="h-4 w-4 text-red-600" />
            <motion.span
              className="absolute inset-0 -mx-1 -my-0.5 rounded bg-red-200/80"
              initial={{ scaleX: 0, originX: 0 }}
              animate={highlighted ? { scaleX: 1 } : { scaleX: 0 }}
              transition={{
                duration: 0.6,
                ease: [0.22, 1, 0.36, 1],
                delay: 0.2,
              }}
            />
            <span className="relative font-semibold text-red-800">
              Due: August 15th, 11:59 PM
            </span>
          </span>
        </>
      ),
    },
    calendar: { month: "August", year: 2025, dayOfWeek: "Friday", dueDay: 15 },
    slides: [
      {
        title: "Neural Networks & Deep Learning",
        subtitle: "A Presentation for CS401",
        bgColor: "bg-white",
        textColor: "text-gray-800",
        highlightColor:
          "text-transparent bg-clip-text bg-gradient-to-r from-blue-500 to-cyan-500",
      },
      {
        title: "What is a Neural Network?",
        points: [
          "Computing systems inspired by biological neural networks.",
          "Composed of interconnected nodes or 'neurons' in layered structures.",
          "Learns from data to perform tasks without explicit programming.",
        ],
        bgColor: "bg-gray-800",
        textColor: "text-white",
        highlightColor: "text-cyan-400",
        image: "https://source.unsplash.com/_11bKldqb1U/800x600",
      },
      {
        title: "Core Architecture",
        points: [
          "Input Layer: Receives the initial data.",
          "Hidden Layers: Perform computations and feature extraction.",
          "Output Layer: Produces the final result (e.g., classification).",
        ],
        bgColor: "bg-white",
        textColor: "text-gray-700",
        highlightColor: "text-blue-600",
        image: "https://source.unsplash.com/-I0I1MifV_g/800x600",
      },
    ],
    roadmap: [
      { icon: Search, label: "Research", time: "Aug 1-3" },
      { icon: GitBranch, label: "Outline", time: "Aug 4" },
      { icon: BookOpen, label: "Draft Content", time: "Aug 5-8" },
      { icon: Presentation, label: "Design Slides", time: "Aug 9-10" },
      { icon: Users, label: "Team Review", time: "Aug 11-13" },
      { icon: Target, label: "Finalize & Submit", time: "Aug 14" },
    ],
  },
  // --- DATASET 2: MARKETING CAMPAIGN (PROFESSIONAL) ---
  {
    id: 2,
    email: {
      subject: "Project Nova: Campaign Launch Plan",
      sender: "Sarah Chen",
      senderEmail: "sarah.chen@innovatech.com",
      topic: "Project Nova Marketing Strategy",
      dueDate: "July 28th, 9:00 AM",
      body: (highlighted: boolean) => (
        <>
          Hi Team,
          <br />
          <br />
          We're greenlit for Project Nova! I need a full marketing and launch
          plan presentation ready for the leadership sync.
          <br />
          <br />
          Let's focus on{" "}
          <span className="relative inline-block">
            <motion.span
              className="absolute inset-0 -mx-1 -my-0.5 rounded bg-purple-200/80"
              initial={{ scaleX: 0, originX: 0 }}
              animate={highlighted ? { scaleX: 1 } : { scaleX: 0 }}
              transition={{ duration: 0.6, ease: [0.22, 1, 0.36, 1] }}
            />
            <span className="relative font-semibold text-gray-900">
              digital channels and influencer outreach
            </span>
          </span>
          . I've attached the initial brief.
          <br />
          <br />
          The deadline is tight, let's make it happen.
          <br />
          <br />
          <span className="relative inline-flex items-center gap-2">
            <Clock className="h-4 w-4 text-red-600" />
            <motion.span
              className="absolute inset-0 -mx-1 -my-0.5 rounded bg-red-200/80"
              initial={{ scaleX: 0, originX: 0 }}
              animate={highlighted ? { scaleX: 1 } : { scaleX: 0 }}
              transition={{
                duration: 0.6,
                ease: [0.22, 1, 0.36, 1],
                delay: 0.2,
              }}
            />
            <span className="relative font-semibold text-red-800">
              Present: July 28th, 9:00 AM
            </span>
          </span>
        </>
      ),
    },
    calendar: { month: "July", year: 2025, dayOfWeek: "Monday", dueDay: 28 },
    slides: [
      {
        title: "Project Nova",
        subtitle: "Go-to-Market Strategy",
        bgColor: "bg-gray-900",
        textColor: "text-white",
        highlightColor:
          "text-transparent bg-clip-text bg-gradient-to-r from-purple-400 to-pink-500",
        fontClass: "font-sans",
      },
      {
        title: "Market Analysis",
        points: [
          "Target Audience: Tech enthusiasts & early adopters (ages 22-40).",
          "Key Competitors: Legacy Solutions Inc., NextGen Corp.",
          "Unique Selling Proposition: 50% faster processing, seamless integration.",
        ],
        bgColor: "bg-white",
        textColor: "text-gray-800",
        highlightColor: "text-purple-600",
        fontClass: "font-sans",
      },
      {
        title: "Campaign Strategy",
        points: [
          "Phase 1 (Awareness): Influencer unboxings, targeted digital ads.",
          "Phase 2 (Consideration): In-depth reviews, webinars.",
          "Phase 3 (Conversion): Limited-time launch offer, remarketing.",
        ],
        bgColor: "bg-white",
        textColor: "text-gray-800",
        highlightColor: "text-purple-600",
        fontClass: "font-sans",
      },
    ],
    roadmap: [
      { icon: Search, label: "Market Research", time: "Jul 14-15" },
      { icon: GitBranch, label: "Strategy Outline", time: "Jul 16" },
      { icon: BookOpen, label: "Develop Creatives", time: "Jul 17-21" },
      { icon: Presentation, label: "Build Deck", time: "Jul 22-23" },
      { icon: Users, label: "Leadership Review", time: "Jul 24" },
      { icon: Target, label: "Final Presentation", time: "Jul 28" },
    ],
  },
  // --- DATASET 3: BIOLOGY LAB REPORT (STUDENT) ---
  {
    id: 3,
    email: {
      subject: "BIO201 Lab Submission: Mitosis",
      sender: "TA David",
      senderEmail: "d.garcia@university.edu",
      topic: "Cellular Mitosis Lab Report",
      dueDate: "October 24th, 5:00 PM",
      body: (highlighted: boolean) => (
        <>
          Hello students,
          <br />
          <br />A reminder that your lab report on{" "}
          <span className="relative inline-block">
            <motion.span
              className="absolute inset-0 -mx-1 -my-0.5 rounded bg-green-200/80"
              initial={{ scaleX: 0, originX: 0 }}
              animate={highlighted ? { scaleX: 1 } : { scaleX: 0 }}
              transition={{ duration: 0.6, ease: [0.22, 1, 0.36, 1] }}
            />
            <span className="relative font-semibold text-gray-900">
              the stages of cellular mitosis
            </span>
          </span>
          is due soon.
          <br />
          <br />
          Please ensure you include detailed diagrams and observations for each
          phase.
          <br />
          <br />
          <span className="relative inline-flex items-center gap-2">
            <Clock className="h-4 w-4 text-red-600" />
            <motion.span
              className="absolute inset-0 -mx-1 -my-0.5 rounded bg-red-200/80"
              initial={{ scaleX: 0, originX: 0 }}
              animate={highlighted ? { scaleX: 1 } : { scaleX: 0 }}
              transition={{
                duration: 0.6,
                ease: [0.22, 1, 0.36, 1],
                delay: 0.2,
              }}
            />
            <span className="relative font-semibold text-red-800">
              Submit by: Oct 24th, 5:00 PM
            </span>
          </span>
        </>
      ),
    },
    calendar: { month: "October", year: 2025, dayOfWeek: "Friday", dueDay: 24 },
    slides: [
      {
        title: "Lab Report: Cellular Mitosis",
        subtitle: "BIO201 - Section B",
        bgColor: "bg-white",
        textColor: "text-gray-700",
        highlightColor: "text-green-600",
        fontClass: "font-sans",
      },
      {
        title: "Prophase",
        points: [
          "Chromatin condenses into visible chromosomes.",
          "The nuclear envelope breaks down.",
          "Spindle fibers begin to form.",
        ],
        bgColor: "bg-emerald-50",
        textColor: "text-gray-700",
        highlightColor: "text-green-600",
        fontClass: "font-sans",
        image: "https://source.unsplash.com/tGBc430E96U/800x600",
      },
      {
        title: "Metaphase",
        points: [
          "Chromosomes align at the metaphase plate.",
          "Each sister chromatid is attached to a spindle fiber.",
        ],
        bgColor: "bg-emerald-50",
        textColor: "text-gray-700",
        highlightColor: "text-green-600",
        fontClass: "font-sans",
        image: "https://source.unsplash.com/q-3L-Sj4f6I/800x600",
      },
    ],
    roadmap: [
      { icon: FlaskConical, label: "Lab Experiment", time: "Oct 13" },
      { icon: Search, label: "Analyze Data", time: "Oct 14-16" },
      { icon: BookOpen, label: "Draft Report", time: "Oct 17-20" },
      { icon: Presentation, label: "Create Diagrams", time: "Oct 21" },
      { icon: Users, label: "Peer Review", time: "Oct 22" },
      { icon: Target, label: "Final Submission", time: "Oct 24" },
    ],
  },
  // --- DATASET 4: HISTORY PRESENTATION (STUDENT) ---
  {
    id: 4,
    email: {
      subject: "HIST101 Group Project",
      sender: "Dr. Anya Sharma",
      senderEmail: "a.sharma@university.edu",
      topic: "The Rise and Fall of the Roman Empire",
      dueDate: "September 19th, 2:00 PM",
      body: (highlighted: boolean) => (
        <>
          Group C,
          <br />
          <br />
          Your assigned presentation topic is{" "}
          <span className="relative inline-block">
            <motion.span
              className="absolute inset-0 -mx-1 -my-0.5 rounded bg-amber-200/80"
              initial={{ scaleX: 0, originX: 0 }}
              animate={highlighted ? { scaleX: 1 } : { scaleX: 0 }}
              transition={{ duration: 0.6, ease: [0.22, 1, 0.36, 1] }}
            />
            <span className="relative font-semibold text-gray-900">
              The Rise and Fall of the Roman Empire
            </span>
          </span>
          .
          <br />
          <br />
          I expect a thorough analysis covering key periods, figures, and
          socio-economic factors.
          <br />
          <br />
          <span className="relative inline-flex items-center gap-2">
            <Clock className="h-4 w-4 text-red-600" />
            <motion.span
              className="absolute inset-0 -mx-1 -my-0.5 rounded bg-red-200/80"
              initial={{ scaleX: 0, originX: 0 }}
              animate={highlighted ? { scaleX: 1 } : { scaleX: 0 }}
              transition={{
                duration: 0.6,
                ease: [0.22, 1, 0.36, 1],
                delay: 0.2,
              }}
            />
            <span className="relative font-semibold text-red-800">
              Presentations start: Sept 19th
            </span>
          </span>
        </>
      ),
    },
    calendar: {
      month: "September",
      year: 2025,
      dayOfWeek: "Friday",
      dueDay: 19,
    },
    slides: [
      {
        title: "The Roman Empire",
        subtitle: "From Republic to Ruin",
        bgColor: "bg-[#FDF6E3]",
        textColor: "text-stone-800",
        highlightColor: "text-red-900",
        fontClass: "font-serif",
      },
      {
        title: "The Roman Republic",
        points: [
          "Founded in 509 BC.",
          "Characterized by a republican government.",
          "Period of significant territorial expansion.",
        ],
        bgColor: "bg-[#FDF6E3]",
        textColor: "text-stone-800",
        highlightColor: "text-red-900",
        fontClass: "font-serif",
      },
      {
        title: "Pax Romana",
        points: [
          "'Roman Peace' - a 200-year period of stability.",
          "Key Emperors: Augustus, Trajan, Marcus Aurelius.",
          "Vast engineering projects: aqueducts, roads.",
        ],
        bgColor: "bg-[#FDF6E3]",
        textColor: "text-stone-800",
        highlightColor: "text-red-900",
        fontClass: "font-serif",
      },
    ],
    roadmap: [
      { icon: Landmark, label: "Primary Source Research", time: "Sep 1-5" },
      { icon: GitBranch, label: "Structure Narrative", time: "Sep 6-8" },
      { icon: BookOpen, label: "Write Script", time: "Sep 9-12" },
      { icon: Presentation, label: "Design Slides", time: "Sep 13-15" },
      { icon: Users, label: "Group Rehearsal", time: "Sep 16-18" },
      { icon: Target, label: "Presentation Day", time: "Sep 19" },
    ],
  },
  // --- DATASET 5: VACATION PLANNING (PERSONAL) ---
  {
    id: 5,
    email: {
      subject: "Your Flight to Kyoto is Confirmed!",
      sender: "SkyHigh Airlines",
      senderEmail: "noreply@skyhigh-airlines.com",
      topic: "Trip to Kyoto, Japan",
      dueDate: "November 8th",
      body: (highlighted: boolean) => (
        <>
          Booking Confirmation: #SH84K2
          <br />
          <br />
          Dear Traveler,
          <br />
          <br />
          Your trip is booked! We're excited to welcome you aboard your flight
          to{" "}
          <span className="relative inline-block">
            <motion.span
              className="absolute inset-0 -mx-1 -my-0.5 rounded bg-rose-200/80"
              initial={{ scaleX: 0, originX: 0 }}
              animate={highlighted ? { scaleX: 1 } : { scaleX: 0 }}
              transition={{ duration: 0.6, ease: [0.22, 1, 0.36, 1] }}
            />
            <span className="relative font-semibold text-gray-900">
              Kyoto, Japan
            </span>
          </span>
          .
          <br />
          <br />
          <span className="relative inline-flex items-center gap-2">
            <Plane className="h-4 w-4 text-blue-600" />
            <motion.span
              className="absolute inset-0 -mx-1 -my-0.5 rounded bg-blue-100/80"
              initial={{ scaleX: 0, originX: 0 }}
              animate={highlighted ? { scaleX: 1 } : { scaleX: 0 }}
              transition={{
                duration: 0.6,
                ease: [0.22, 1, 0.36, 1],
                delay: 0.2,
              }}
            />
            <span className="relative font-semibold text-blue-800">
              Departure: November 8th
            </span>
          </span>
        </>
      ),
    },
    calendar: {
      month: "November",
      year: 2025,
      dayOfWeek: "Saturday",
      dueDay: 8,
    },
    slides: [
      {
        title: "Kyoto, Japan",
        subtitle: "Autumn Itinerary",
        bgColor: "bg-rose-50",
        textColor: "text-gray-800",
        highlightColor: "text-red-500",
        image: "https://source.unsplash.com/O6v3a2Y/1600x900",
      },
      {
        title: "Day 1-2: Arrival & Arashiyama",
        points: [
          "Arrive at KIX, transfer to Kyoto.",
          "Check into hotel in Gion.",
          "Explore Arashiyama Bamboo Grove & Tenryū-ji Temple.",
        ],
        bgColor: "bg-white",
        textColor: "text-gray-700",
        highlightColor: "text-red-500",
      },
      {
        title: "Day 3-4: Temples & Culture",
        points: [
          "Visit Kinkaku-ji (Golden Pavilion) & Fushimi Inari Shrine.",
          "Walk through the historic Gion district.",
          "Attend a traditional tea ceremony.",
        ],
        bgColor: "bg-white",
        textColor: "text-gray-700",
        highlightColor: "text-red-500",
      },
    ],
    roadmap: [
      { icon: BedDouble, label: "Book Hotels", time: "By Aug 30" },
      { icon: Landmark, label: "Plan Daily Activities", time: "By Sep 15" },
      { icon: ShoppingCart, label: "Buy Rail Pass", time: "By Oct 1" },
      { icon: Briefcase, label: "Pack Bags", time: "Nov 6" },
      { icon: Plane, label: "Flight Day!", time: "Nov 8" },
    ],
  },
];
