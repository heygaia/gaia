import { Button } from "@heroui/button";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Contact Us",
  description:
    "Need help with GAIA? Contact our support team for assistance and inquiries.",
  openGraph: {
    title: "Contact Us",
    description:
      "Need help with GAIA? Contact our support team for assistance and inquiries.",
    url: "https://heygaia.io/contact",
    images: ["/images/screenshot.webp"],
    siteName: "GAIA - Your Personal Assistant",
    type: "website",
  },
  twitter: {
    card: "summary_large_image",
    title: "Contact Us",
    description:
      "Need help with GAIA? Contact our support team for assistance and inquiries.",
    images: ["/images/screenshot.webp"],
  },
};

export default function ContactPage() {
  return (
    <div className="bg-custom-gradient flex min-h-screen w-screen items-center justify-center p-6">
      <div className="w-full max-w-lg rounded-2xl bg-zinc-900 p-8 text-center shadow-lg">
        <h1 className="text-2xl font-bold">Need Help?</h1>
        <p className="mt-2 text-zinc-300">
          For any assistance or inquiries, feel free to reach out to us.
        </p>
        <a
          href="mailto:support@heygaia.io"
          className="mt-4 inline-block"
          aria-label="Email GAIA Support"
        >
          <Button color="primary" size="lg" variant="shadow" radius="full">
            Email us at: <b>support@heygaia.io</b>
          </Button>
        </a>
      </div>
    </div>
  );
}
