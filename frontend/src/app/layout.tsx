import "./styles/globals.css";

import type { Metadata, Viewport } from "next";
import Script from "next/script";

import ProvidersLayout from "@/layouts/ProvidersLayout";

import AnalyticsLayout from "@/layouts/AnalyticsLayout";
import { defaultFont, getAllFontVariables } from "./fonts";
import { Suspense } from "react";

export const metadata: Metadata = {
  metadataBase: new URL("https://heygaia.io"),
  title: { default: "GAIA - Your Personal Assistant", template: "%s | GAIA" },
  description:
    "GAIA is your personal AI assistant designed to help increase your productivity.",
  icons: {
    icon: [
      { url: "/favicon.ico", type: "image/x-icon" },
      { url: "/favicon-32x32.png", type: "image/png", sizes: "32x32" },
      { url: "/favicon-16x16.png", type: "image/png", sizes: "16x16" },
    ],
    apple: "/apple-touch-icon.png",
  },
  manifest: "/site.webmanifest",
  keywords: [
    "GAIA",
    "Personal AI Assistant",
    "AI",
    "ai assistant",
    "digital assistant",
    "productivity",
    "Hey GAIA",
    "general purpose ai assistant",
    "artificial intelligence",
    "virtual assistant",
    "smart assistant",
    "AI personal assistant",
    "task management",
  ],
  openGraph: {
    title: "GAIA - Your Personal Assistant",
    siteName: "GAIA - Personal Assistant",
    url: "https://heygaia.io/",
    type: "website",
    description:
      "GAIA is your personal AI assistant designed to help increase your productivity.",
    images: ["/landing/screenshot.webp"],
  },
  twitter: {
    card: "summary_large_image",
    title: "GAIA - Your Personal Assistant",
    description:
      "GAIA is your personal AI assistant designed to help increase your productivity.",
    images: ["/landing/screenshot.webp"],
  },
  other: {
    "msapplication-TileColor": "#00bbff",
    "apple-mobile-web-app-capable": "yes",
  },
};

export const viewport: Viewport = {
  themeColor: "#00bbff",
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" className={`${getAllFontVariables()} dark`}>
      <body className={`dark ${defaultFont.className}`}>
        <main>
          <ProvidersLayout>{children}</ProvidersLayout>
        </main>
        <Script
          async
          src="https://accounts.google.com/gsi/client"
          strategy="lazyOnload"
        />

        {/* JSON-LD Schema */}
        <Script id="json-ld" type="application/ld+json">
          {JSON.stringify({
            "@context": "https://schema.org",
            "@type": "WebSite",
            name: "GAIA",
            alternateName: ["G.A.I.A", "General Purpose AI Assistant"],
            url: "https://heygaia.io",
          })}
        </Script>

        {/* Better Stack widget for API Uptime */}
        <Script
          src="https://uptime.betterstack.com/widgets/announcement.js"
          data-id="212836"
          async
          type="text/javascript"
          strategy="lazyOnload"
        />

        <Suspense fallback={<></>}>
          <AnalyticsLayout />
        </Suspense>
      </body>
    </html>
  );
}
