import "./styles/tailwind.css";

import { Databuddy } from "@databuddy/sdk/react";
import type { Metadata, Viewport } from "next";
import Script from "next/script";
import { Suspense } from "react";

import AnalyticsLayout from "@/layouts/AnalyticsLayout";
import ProvidersLayout from "@/layouts/ProvidersLayout";

import { defaultFont, getAllFontVariables } from "./fonts";

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
    images: ["/images/screenshot.webp"],
  },
  twitter: {
    card: "summary_large_image",
    title: "GAIA - Your Personal Assistant",
    description:
      "GAIA is your personal AI assistant designed to help increase your productivity.",
    images: ["/images/screenshot.webp"],
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
      <head>
        <link
          rel="preconnect"
          href="https://status.heygaia.io"
          crossOrigin="anonymous"
        />
        <link rel="dns-prefetch" href="https://uptime.betterstack.com" />
        <link rel="dns-prefetch" href="https://us.i.posthog.com" />
      </head>
      <body className={`dark ${defaultFont.className}`}>
        <main>
          <ProvidersLayout>{children}</ProvidersLayout>
        </main>

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
        {/* Rybbit Analytics */}
        <Script
          src="https://analytics.heygaia.io/api/script.js"
          data-site-id="1"
          defer
          data-session-replay="true"
        />

        {process.env.NEXT_PUBLIC_DATABUDDY_CLIENT_ID && (
          <Databuddy
            clientId={process.env.NEXT_PUBLIC_DATABUDDY_CLIENT_ID}
            trackHashChanges
            trackAttributes
            trackOutgoingLinks
            trackInteractions
            trackEngagement
            trackScrollDepth
            trackExitIntent
            trackBounceRate
            trackWebVitals
            trackErrors
            enableBatching
            batchSize={20}
            batchTimeout={5000}
            disabled={process.env.NODE_ENV === "development"}
          />
        )}
      </body>
    </html>
  );
}
