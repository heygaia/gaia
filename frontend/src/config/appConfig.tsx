import { ReactElement } from "react";

import {
  BookOpen02Icon,
  BubbleConversationChatIcon,
  CreditCardPosIcon,
  CustomerService01Icon,
  DiscordIcon,
  Github,
  GlobalIcon,
  Home01Icon,
  Idea01Icon,
  LinkedinIcon,
  MapsIcon,
  TwitterIcon,
  WhatsappIcon,
} from "@/components/shared/icons";

export interface AppLink {
  label: string;
  href: string;
  icon?: ReactElement;
  external?: boolean;
  requiresAuth?: boolean;
  guestOnly?: boolean;
  commented?: boolean;
}

export interface LinkSection {
  title: string;
  links: AppLink[];
}

export const appConfig = {
  // Site information
  site: {
    name: "GAIA",
    copyright: "© 2025 GAIA",
    domain: "heygaia.io",
  },

  // All links organized by category
  links: {
    // Primary navigation links (used in navbar)
    main: [
      {
        href: "/",
        label: "Home",
        icon: <Home01Icon width={19} color={undefined} />,
      },
    ] as AppLink[],

    // Navigation menu sections
    product: [
      // {
      //   href: "/features",
      //   label: "Features",
      //   icon: <BookOpen02Icon width={19} color={undefined} />,
      // },
      {
        href: "https://gaia.featurebase.app/roadmap",
        label: "Roadmap",
        icon: <MapsIcon width={19} color={undefined} />,
        external: true,
      },
      {
        href: "https://status.heygaia.io",
        label: "Status",
        icon: <GlobalIcon width={19} color={undefined} />,
        external: true,
      },
      //   {
      //     href: "/use-cases",
      //     label: "Use Cases",
      //     icon: <BookOpen02Icon width={19} color={undefined} />,
      //   },
    ] as AppLink[],

    resources: [
      {
        href: "/blog",
        label: "Blog",
        icon: <BookOpen02Icon width={19} color={undefined} />,
      },
      {
        href: "https://docs.heygaia.io",
        label: "Docs",
        icon: <BookOpen02Icon width={19} color={undefined} />,
        external: true,
      },
      {
        href: "/pricing",
        label: "Pricing",
        icon: <CreditCardPosIcon width={19} color={undefined} />,
      },
      {
        href: "https://gaia.featurebase.app",
        label: "Feature Request",
        icon: <Idea01Icon width={19} color={undefined} />,
        external: true,
      },
    ] as AppLink[],

    company: [
      {
        href: "/about",
        label: "About",
        icon: <GlobalIcon width={19} color={undefined} />,
      },
      {
        href: "/contact",
        label: "Contact",
        icon: <CustomerService01Icon width={19} color={undefined} />,
      },
      {
        href: "/terms",
        label: "Terms",
        icon: <BookOpen02Icon width={19} color={undefined} />,
      },
      {
        href: "/privacy",
        label: "Privacy",
        icon: <BookOpen02Icon width={19} color={undefined} />,
      },
    ] as AppLink[],

    connect: [
      {
        href: "https://discord.heygaia.io",
        label: "Discord",
        icon: <DiscordIcon width={19} />,
        external: true,
      },
      {
        href: "https://x.com/_heygaia",
        label: "Twitter (X)",
        icon: <TwitterIcon width={19} />,
        external: true,
      },
      {
        href: "https://github.com/heygaia",
        label: "GitHub",
        icon: <Github width={19} />,
        external: true,
      },
      {
        href: "https://whatsapp.heygaia.io",
        label: "WhatsApp",
        icon: <WhatsappIcon width={19} />,
        external: true,
      },
      {
        href: "https://youtube.com/@heygaia_io",
        label: "YouTube",
        icon: <WhatsappIcon width={19} />,
        external: true,
      },
    ] as AppLink[],

    // Authentication related links
    auth: [
      {
        href: "/c",
        label: "Chat",
        icon: <BubbleConversationChatIcon width={17} color={undefined} />,
        requiresAuth: true,
      },
      {
        href: "/signup",
        label: "Get Started",
        guestOnly: true,
      },
    ] as AppLink[],

    // Explore links
    explore: [
      {
        label: "About",
        href: "/about",
        icon: <GlobalIcon width={19} />,
      },
      {
        label: "Blog",
        href: "/blog",
        icon: <BookOpen02Icon width={19} />,
      },
      {
        label: "Status",
        href: "https://status.heygaia.io",
        external: true,
        icon: <BookOpen02Icon width={19} />,
      },
    ] as AppLink[],

    // Social/Connect links
    social: [
      {
        label: "Contact Us",
        href: "/contact",
        icon: <CustomerService01Icon width={19} />,
      },
      {
        label: "X (Twitter)",
        href: "https://x.com/_heygaia",
        external: true,
        icon: <TwitterIcon width={19} />,
      },
      {
        label: "WhatsApp",
        href: "https://whatsapp.heygaia.io",
        external: true,
        icon: <WhatsappIcon width={19} />,
      },
      {
        label: "GitHub",
        href: "https://github.com/heygaia",
        external: true,
        icon: <Github width={19} />,
      },
      {
        label: "LinkedIn",
        href: "https://www.linkedin.com/company/heygaia",
        external: true,
        icon: <LinkedinIcon width={19} />,
      },
    ] as AppLink[],

    // Legal links
    legal: [
      { label: "Terms", href: "/terms" },
      { label: "Privacy", href: "/privacy" },
    ] as AppLink[],
  },

  // Footer sections (organized for footer display)
  footerSections: [
    {
      title: "Get Started",
      links: [
        // Get auth links that are guest-only or require auth
        { label: "Login", href: "/login", guestOnly: true },
        { label: "Signup", href: "/signup", guestOnly: true },
        { label: "New Chat", href: "/c", requiresAuth: true },
      ],
    },
    {
      title: "Explore",
      links: [
        // Combine explore links with main navigation links that fit here
        { label: "About", href: "/about", icon: <GlobalIcon width={19} /> },
        { label: "Blog", href: "/blog", icon: <BookOpen02Icon width={19} /> },
        {
          label: "Feature Request",
          href: "https://gaia.featurebase.app",
          external: true,
          icon: <Idea01Icon width={19} />,
        },
        {
          label: "Roadmap",
          href: "https://gaia.featurebase.app/roadmap",
          external: true,
          icon: <MapsIcon width={19} />,
        },
        {
          label: "Pricing",
          href: "/pricing",
          icon: <CreditCardPosIcon width={19} />,
        },
        {
          label: "Status",
          href: "https://status.heygaia.io",
          external: true,
          icon: <BookOpen02Icon width={19} />,
        },
      ],
    },
    {
      title: "Connect",
      links: [
        // Use social links + Discord from main nav
        {
          label: "Contact Us",
          href: "/contact",
          icon: <CustomerService01Icon width={19} />,
        },
        {
          label: "X (Twitter)",
          href: "https://x.com/_heygaia",
          external: true,
          icon: <TwitterIcon width={19} />,
        },
        {
          label: "Discord",
          href: "https://discord.heygaia.io",
          external: true,
          icon: <DiscordIcon width={19} />,
        },
        {
          label: "WhatsApp",
          href: "https://whatsapp.heygaia.io",
          external: true,
          icon: <WhatsappIcon width={19} />,
        },
        {
          label: "GitHub",
          href: "https://github.com/heygaia",
          external: true,
          icon: <Github width={19} />,
        },
        {
          label: "LinkedIn",
          href: "https://www.linkedin.com/company/heygaia",
          external: true,
          icon: <LinkedinIcon width={19} />,
        },
      ],
    },
    {
      title: "Legal",
      links: [
        { label: "Terms", href: "/terms" },
        { label: "Privacy", href: "/privacy" },
      ],
    },
  ] as LinkSection[],
};

// Export legacy aliases for easier migration
export const siteConfig = {
  name: appConfig.site.name,
  copyright: appConfig.site.copyright,
  domain: appConfig.site.domain,
  pageSections: appConfig.footerSections,
};

export const mainNavLinks = appConfig.links.main;
export const authNavLinks = appConfig.links.auth;
export const productNavLinks = appConfig.links.product;
export const resourcesNavLinks = appConfig.links.resources;
export const companyNavLinks = appConfig.links.company;
export const connectNavLinks = appConfig.links.connect;
