import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Blog",
  description:
    "Explore the latest posts from GAIA, the creators of the AI personal assistant",

  openGraph: {
    title: "Blog",
    description:
      "Explore the latest posts from GAIA, the creators of the AI personal assistant",
    url: "https://heygaia.io/blog",
    images: ["/images/screenshot.webp"],
    siteName: "GAIA - Your Personal Assistant",
    type: "website",
  },
  twitter: {
    card: "summary_large_image",
    title: "Blog",
    description:
      "Explore the latest posts from GAIA, the creators of the AI personal assistant",
    images: ["/images/screenshot.webp"],
  },
};

export default function BlogLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return children;
}
