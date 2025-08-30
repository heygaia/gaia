export interface UseCase {
  title: string;
  description: string;
  action_type: "prompt" | "workflow";
  integrations: string[];
  categories: string[];
  published_id: string;
  prompt?: string;
}

export const useCasesData: UseCase[] = [
  // Students
  {
    title: "Study Schedule Generator",
    description:
      "Automatically create personalized study schedules based on your courses, exams, and preferences",
    action_type: "workflow",
    integrations: ["calendar", "notion", "productivity"],
    categories: ["Students", "featured"],
    published_id: "study-schedule-workflow",
  },
  {
    title: "Essay Writing Assistant",
    description:
      "Get structured help with essay planning, research guidance, and writing improvement",
    action_type: "prompt",
    integrations: ["search", "documents", "creative"],
    categories: ["Students"],
    published_id: "essay-writing-prompt",
    prompt:
      "You are an expert writing tutor. Help me structure and improve my essay on [TOPIC]. First, analyze the topic and suggest a clear thesis statement. Then, provide an outline with main points and supporting evidence. Finally, review my draft and suggest improvements for clarity, flow, and academic style.",
  },
  {
    title: "Study Buddy Q&A",
    description:
      "Get help understanding complex concepts, practice problems, and exam preparation",
    action_type: "prompt",
    integrations: ["search", "memory", "creative"],
    categories: ["Students"],
    published_id: "study-buddy-prompt",
    prompt:
      "You are a knowledgeable tutor in [SUBJECT]. Help me understand [CONCEPT/TOPIC]. Please: 1) Explain the concept in simple terms with real-world examples, 2) Break down complex ideas into digestible parts, 3) Provide practice questions to test my understanding, 4) Suggest study techniques and memory aids, 5) Connect this topic to related concepts I should know.",
  },

  // Founders
  {
    title: "Pitch Deck Generator",
    description:
      "Create compelling investor pitch decks with market analysis, financial projections, and compelling narratives",
    action_type: "workflow",
    integrations: ["creative", "google_docs", "productivity"],
    categories: ["Founders", "featured"],
    published_id: "pitch-deck-workflow",
  },
  {
    title: "Startup Idea Validator",
    description:
      "Validate your startup idea with market research, feasibility analysis, and competitive assessment",
    action_type: "prompt",
    integrations: ["search", "memory", "documents"],
    categories: ["Founders"],
    published_id: "startup-validator-prompt",
    prompt:
      "You are a startup advisor and venture capitalist. Help me validate my startup idea: [STARTUP IDEA]. Please analyze: 1) Market opportunity and target customer needs, 2) Competitive landscape and differentiation, 3) Business model viability and revenue potential, 4) Technical feasibility and resource requirements, 5) Key risks and mitigation strategies. Provide honest feedback and actionable next steps.",
  },
  {
    title: "Market Research Analyzer",
    description:
      "Analyze market opportunities, competitor landscape, and validate your business idea",
    action_type: "prompt",
    integrations: ["search", "memory", "documents"],
    categories: ["Founders"],
    published_id: "market-research-prompt",
    prompt:
      "Act as a senior business analyst. I'm developing [BUSINESS IDEA] targeting [TARGET MARKET]. Please provide: 1) Market size analysis and growth potential, 2) Key competitors and their positioning, 3) Unique value proposition opportunities, 4) Potential challenges and risks, 5) Go-to-market strategy recommendations. Use data-driven insights and industry best practices.",
  },

  // Engineering
  {
    title: "Code Review Automation",
    description:
      "Automatically review code commits, check for best practices, and suggest improvements",
    action_type: "workflow",
    integrations: ["development", "productivity", "mail"],
    categories: ["Engineering"],
    published_id: "code-review-workflow",
  },
  {
    title: "Debug Helper Assistant",
    description:
      "Get help debugging code issues, understanding error messages, and finding solutions",
    action_type: "prompt",
    integrations: ["development", "search", "memory"],
    categories: ["Engineering"],
    published_id: "debug-helper-prompt",
    prompt:
      "You are a senior software engineer debugging expert. I'm facing this issue: [ERROR/PROBLEM DESCRIPTION]. Here's my code: [CODE]. Please help me: 1) Identify the root cause of the issue, 2) Explain why this error occurs, 3) Provide step-by-step debugging approach, 4) Suggest specific fixes with code examples, 5) Recommend best practices to prevent similar issues. Be thorough and educational.",
  },
  {
    title: "Architecture Design Helper",
    description:
      "Get expert guidance on system architecture, design patterns, and technical decisions",
    action_type: "prompt",
    integrations: ["development", "memory", "creative"],
    categories: ["Engineering"],
    published_id: "architecture-design-prompt",
    prompt:
      "You are a senior software architect. I'm building [SYSTEM DESCRIPTION] with requirements: [REQUIREMENTS]. Please provide: 1) Recommended system architecture with key components, 2) Suitable design patterns and why, 3) Technology stack recommendations, 4) Scalability considerations, 5) Potential bottlenecks and mitigation strategies. Focus on maintainability, performance, and best practices.",
  },

  // Marketing
  {
    title: "Social Media Campaign Creator",
    description:
      "Generate comprehensive social media campaigns with content calendar and engagement strategies",
    action_type: "workflow",
    integrations: ["creative", "calendar", "productivity"],
    categories: ["Marketing", "featured"],
    published_id: "social-media-campaign-workflow",
  },
  {
    title: "Brand Voice Generator",
    description:
      "Develop consistent brand voice, messaging guidelines, and content tone for your business",
    action_type: "prompt",
    integrations: ["creative", "memory", "documents"],
    categories: ["Marketing"],
    published_id: "brand-voice-prompt",
    prompt:
      "You are a brand strategist and copywriter. Help me develop a distinctive brand voice for [BUSINESS/BRAND] targeting [TARGET AUDIENCE]. Please create: 1) Brand personality traits and characteristics, 2) Tone of voice guidelines (formal/casual, friendly/professional, etc.), 3) Key messaging pillars and value propositions, 4) Do's and don'ts for content creation, 5) Example content pieces showing the brand voice in action. Make it authentic and memorable.",
  },
  {
    title: "Content Strategy Planner",
    description:
      "Develop content strategies, topics, and distribution plans for your target audience",
    action_type: "prompt",
    integrations: ["creative", "search", "memory"],
    categories: ["Marketing"],
    published_id: "content-strategy-prompt",
    prompt:
      "As a content marketing strategist, help me create a content plan for [BUSINESS/BRAND] targeting [AUDIENCE]. Please provide: 1) Content pillars and themes that resonate with the audience, 2) Content types and formats for maximum engagement, 3) Publishing frequency and optimal timing, 4) Distribution channels and promotion strategy, 5) KPIs to track success. Make it actionable and data-driven.",
  },

  // Knowledge Workers
  {
    title: "Meeting Minutes Summarizer",
    description:
      "Automatically transcribe meetings, extract action items, and distribute summaries to participants",
    action_type: "workflow",
    integrations: ["documents", "mail", "productivity"],
    categories: ["Knowledge Workers"],
    published_id: "meeting-minutes-workflow",
  },
  {
    title: "Decision Framework Helper",
    description:
      "Structure complex decisions with pros/cons analysis, risk assessment, and recommendation frameworks",
    action_type: "prompt",
    integrations: ["memory", "documents", "productivity"],
    categories: ["Knowledge Workers"],
    published_id: "decision-framework-prompt",
    prompt:
      "You are a strategic decision consultant. I need help making this decision: [DECISION DESCRIPTION]. Please help me: 1) Structure the decision with clear options and criteria, 2) Analyze pros and cons for each option, 3) Assess risks and potential outcomes, 4) Consider short-term vs long-term implications, 5) Provide a recommendation with clear reasoning. Use a systematic decision-making framework.",
  },
  {
    title: "Research Synthesis Assistant",
    description:
      "Synthesize information from multiple sources into coherent insights and recommendations",
    action_type: "prompt",
    integrations: ["search", "memory", "documents"],
    categories: ["Knowledge Workers"],
    published_id: "research-synthesis-prompt",
    prompt:
      "You are a research analyst expert. I've gathered information about [RESEARCH TOPIC] from various sources. Please help me: 1) Identify key themes and patterns across the sources, 2) Synthesize main findings and insights, 3) Highlight conflicting viewpoints and their validity, 4) Draw actionable conclusions and recommendations, 5) Suggest areas for further investigation. Present findings in a structured, executive-friendly format.",
  },

  // Business & Ops
  {
    title: "Invoice Processing System",
    description:
      "Automate invoice processing, approval workflows, and payment scheduling",
    action_type: "workflow",
    integrations: ["documents", "mail", "productivity"],
    categories: ["Business & Ops"],
    published_id: "invoice-processing-workflow",
  },
  {
    title: "Team Performance Analyzer",
    description:
      "Analyze team productivity, identify bottlenecks, and recommend improvements for better collaboration",
    action_type: "prompt",
    integrations: ["productivity", "memory", "documents"],
    categories: ["Business & Ops"],
    published_id: "team-performance-prompt",
    prompt:
      "You are an organizational efficiency expert. Help me analyze my team's performance. Team details: [TEAM DESCRIPTION] and current challenges: [CHALLENGES]. Please provide: 1) Performance metrics and KPI analysis, 2) Identification of productivity bottlenecks, 3) Communication and collaboration improvement suggestions, 4) Process optimization recommendations, 5) Action plan with measurable goals. Focus on practical, implementable solutions.",
  },
  {
    title: "Process Optimization Consultant",
    description:
      "Analyze business processes and recommend efficiency improvements and automation opportunities",
    action_type: "prompt",
    integrations: ["productivity", "memory", "documents"],
    categories: ["Business & Ops"],
    published_id: "process-optimization-prompt",
    prompt:
      "Act as a business process consultant. I want to optimize [PROCESS NAME] in my organization. Current process: [PROCESS DESCRIPTION]. Please provide: 1) Process inefficiencies and bottlenecks analysis, 2) Automation opportunities and tools, 3) Workflow improvements and reorganization suggestions, 4) Resource optimization recommendations, 5) Implementation roadmap with priorities. Focus on measurable improvements and ROI.",
  },
];
