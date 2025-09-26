import { ReactElement } from "react";

import {
  BookOpen02Icon,
  BubbleConversationChatIcon,
  Calendar01Icon,
  CreditCardPosIcon,
  CustomerService01Icon,
  DiscordIcon,
  Github,
  GlobalIcon,
  HeartHandIcon,
  Home01Icon,
  Idea01Icon,
  LinkedinIcon,
  MapsIcon,
  QuillWrite01Icon,
  TwitterIcon,
  WhatsappIcon,
  YoutubeIcon,
} from "@/components/shared/icons";
import { BookAIcon, BookTemplateIcon } from "lucide-react";

export interface AppLink {
  label: string;
  href: string;
  icon?: ReactElement;
  external?: boolean;
  requiresAuth?: boolean;
  guestOnly?: boolean;
  commented?: boolean;
  description?: string;
  hideFooter?: boolean;
}

export interface LinkSection {
  title: string;
  links: AppLink[];
}

export const appConfig = {
  // Site information
  site: {
    name: "GAIA",
    copyright: "Copyright © 2025 GAIA. All rights reserved.",
    domain: "heygaia.io",
  },

  // Core link definitions - single source of truth
  links: {
    // Primary navigation links (used in navbar)
    main: [
      {
        href: "/",
        label: "Home",
        icon: <Home01Icon width={22} height={22} color={undefined} />,
        description: "Return to the home page",
      },
    ] as AppLink[],

    // Navigation menu sections
    product: [
      {
        href: "/login",
        label: "Get Started",
        icon: (
          <BubbleConversationChatIcon
            width={22}
            height={22}
            color={undefined}
          />
        ),
        requiresAuth: false,
        description: "Sign Up / Login to GAIA",
      },
      {
        href: "/goals",
        label: "Goals",
        icon: <MapsIcon width={22} height={22} color={undefined} />,
        requiresAuth: true,
        description: "Create and track your goals",
      },
      {
        href: "/todos",
        label: "Todos",
        icon: <Idea01Icon width={22} height={22} color={undefined} />,
        requiresAuth: true,
        description: "Manage your tasks and projects",
      },
      {
        href: "/calendar",
        label: "Calendar",
        icon: <Calendar01Icon width={22} height={22} color={undefined} />,
        requiresAuth: true,
        description: "Schedule and manage events",
      },
      {
        href: "/mail",
        label: "Mail",
        icon: (
          <CustomerService01Icon width={22} height={22} color={undefined} />
        ),
        requiresAuth: true,
        description: "Manage your emails",
      },
      {
        href: "/workflows",
        label: "Workflows",
        icon: <Idea01Icon width={22} height={22} color={undefined} />,
        requiresAuth: true,
        description: "Create automated workflows",
      },
    ] as AppLink[],

    resources: [
      {
        href: "/use-cases",
        label: "Use Cases",
        icon: <Idea01Icon width={22} height={22} color={undefined} />,
        description: "Discover workflows and AI prompts",
      },
      {
        href: "/blog",
        label: "Blog",
        icon: <QuillWrite01Icon width={22} height={22} color={undefined} />,
        description: "Read the latest updates and insights",
      },
      {
        href: "https://docs.heygaia.io",
        label: "Documentation",
        icon: <BookOpen02Icon width={22} height={22} color={undefined} />,
        external: true,
        description: "Comprehensive documentation and guides",
      },
      {
        href: "/pricing",
        label: "Pricing",
        icon: <CreditCardPosIcon width={22} height={22} color={undefined} />,
        description: "Choose the perfect plan for your needs",
      },
      {
        href: "https://gaia.featurebase.app",
        label: "Request a Feature",
        icon: <Idea01Icon width={22} height={22} color={undefined} />,
        external: true,
        description: "Request new features and vote on ideas",
      },
      {
        href: "https://gaia.featurebase.app/roadmap",
        label: "Roadmap",
        icon: <MapsIcon width={22} height={22} color={undefined} />,
        external: true,
        description: "See what's coming next",
      },
      {
        href: "https://status.heygaia.io",
        label: "Status",
        icon: <GlobalIcon width={22} height={22} color={undefined} />,
        external: true,
        description: "Check the status of GAIA services",
      },
    ] as AppLink[],

    company: [
      {
        href: "/manifesto",
        label: "Manifesto",
        icon: <GlobalIcon width={22} height={22} color={undefined} />,
        description: "Learn about our mission",
      },
      {
        href: "/contact",
        label: "Contact",
        icon: <HeartHandIcon width={22} height={22} color={undefined} />,
        description: "Get in touch with our team",
      },
      {
        href: "/terms",
        label: "Terms",
        icon: <BookOpen02Icon width={22} height={22} color={undefined} />,
        description: "Terms of service and usage",
        hideFooter: true,
      },
      {
        href: "/privacy",
        label: "Privacy",
        icon: <BookOpen02Icon width={22} height={22} color={undefined} />,
        description: "Our privacy policy",
        hideFooter: true,
      },
    ] as AppLink[],

    connect: [
      {
        href: "https://discord.heygaia.io",
        label: "Discord",
        icon: <DiscordIcon width={22} height={22} />,
        external: true,
        description: "Join Discord Community",
      },
      {
        href: "https://x.com/_heygaia",
        label: "Twitter (X)",
        icon: <TwitterIcon width={22} height={22} />,
        external: true,
        description: "Follow us for updates",
      },
      {
        href: "https://github.com/heygaia",
        label: "GitHub",
        icon: <Github width={22} height={22} />,
        external: true,
        description: "Check out our open source projects",
      },
      {
        href: "https://whatsapp.heygaia.io",
        label: "WhatsApp",
        icon: <WhatsappIcon width={22} height={22} />,
        external: true,
        description: "Join WhatsApp Community",
      },
      {
        href: "https://youtube.com/@heygaia_io",
        label: "YouTube",
        icon: <YoutubeIcon width={22} height={22} />,
        external: true,
        description: "Subscribe to our YouTube Channel",
      },
      {
        href: "https://www.linkedin.com/company/heygaia",
        label: "LinkedIn",
        icon: <LinkedinIcon width={22} height={22} />,
        external: true,
        description: "Follow our LinkedIn Company Page",
      },
    ] as AppLink[],

    // Authentication related links
    auth: [
      {
        href: "/login",
        label: "Login",
        guestOnly: true,
      },
      {
        href: "/signup",
        label: "Get Started",
        guestOnly: true,
      },
      {
        href: "/c",
        label: "Chat",
        icon: <BubbleConversationChatIcon width={17} color={undefined} />,
        requiresAuth: true,
      },
    ] as AppLink[],
  },

  // Footer mapping - references existing link categories
  footerMapping: {
    Product: ["product"],
    Resources: ["resources"],
    Company: ["company"],
  } as Record<string, string[]>,
};

// Utility functions for footer generation
const getFooterSections = (): LinkSection[] => {
  return Object.entries(appConfig.footerMapping).map(([title, categories]) => ({
    title,
    links: categories.flatMap(
      (category) =>
        appConfig.links[category as keyof typeof appConfig.links] || [],
    ),
  }));
};

// Streamlined exports
export const footerSections = getFooterSections();

// Direct access to link categories for navigation
export const { main, product, resources, company, connect, auth } =
  appConfig.links;

// Utility function to get description for a link by label
export const getLinkDescription = (label: string): string => {
  const allLinks = Object.values(appConfig.links).flat();
  const link = allLinks.find((link) => link.label === label);
  return link?.description || "";
};

// Utility function to get a link by label from all categories
export const getLinkByLabel = (label: string): AppLink | undefined => {
  const allLinks = Object.values(appConfig.links).flat();
  return allLinks.find((link) => link.label === label);
};
