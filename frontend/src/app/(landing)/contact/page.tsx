import type { Metadata } from "next";

import ContactForm from "@/features/contact/components/ContactForm";
import ContactSidebar from "@/features/contact/components/ContactSidebar";

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
    <main className="flex h-screen w-screen flex-col items-center justify-center bg-gradient-to-b from-zinc-900 to-black px-6 py-16">
      <header className="text-center">
        <h1 className="text-5xl font-semibold tracking-tight text-balance">
          Contact us
        </h1>
        <p className="mt-3 text-foreground-500">
          Get in touch with our team for support, feature requests, or general
          inquiries.
        </p>
      </header>

      <section className="mt-16 grid w-full max-w-5xl gap-10 md:grid-cols-[250px_1fr]">
        <aside className="border-zinc-800 md:border-r md:pr-10">
          <ContactSidebar />
        </aside>

        <section>
          <h2 id="inquiries-heading" className="mb-4 text-lg font-medium">
            Send us a message
          </h2>
          <ContactForm aria-labelledby="inquiries-heading" />
        </section>
      </section>
    </main>
  );
}
