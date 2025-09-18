import type { Metadata } from "next";
import Image from "next/image";
import { Suspense } from "react";
import ReactMarkdown from "react-markdown";

import { AuthorTooltip } from "@/features/blog/components/AuthorTooltip";
import type { AboutData, Author } from "@/types/api/aboutApiTypes";
export const metadata: Metadata = {
  title: "About",
  description:
    "Learn more about GAIA, your personal AI assistant designed to enhance productivity, automate tasks, and assist in daily activities.",
  openGraph: {
    title: "About",
    siteName: "GAIA - Personal Assistant",
    url: "https://heygaia.io/about",
    type: "website",
    description:
      "Learn more about GAIA, your personal AI assistant designed to enhance productivity, automate tasks, and assist in daily activities.",
    images: ["/landing/screenshot.webp"],
  },
  twitter: {
    card: "summary_large_image",
    title: "About",
    description:
      "Learn more about GAIA, your personal AI assistant designed to enhance productivity, automate tasks, and assist in daily activities.",
    images: ["/landing/screenshot.webp"],
  },
  keywords: [
    "GAIA",
    "About GAIA",
    "AI Assistant",
    "Artificial Intelligence",
    "Productivity Assistant",
    "Virtual Assistant",
    "Smart Assistant",
    "AI Personal Assistant",
    "Task Management",
    "Automation",
  ],
};

export default async function About() {
  const aboutData: AboutData | null = {
    content:
      "Hey, I’m building GAIA because I’ve always wanted a personal assistant that actually does things for me—not just answer questions or pretend to help. The truth is, tools like Siri, Alexa, and even ChatGPT are helpful in small ways, but they’re not real assistants.\n\nThey don’t remember you, they don’t handle your work, and they don’t make your life easier the way a human would.\n\nGAIA is our attempt to change that.\n\nWe’re building a general-purpose personal assistant that’s always by your side. It connects to your digital life, learns how you work, and starts taking care of the boring stuff—emails, meetings, scheduling, reminders, calls, your goals, your habits—so you can focus on what actually matters.\n\nIt’s not a chatbot. It’s an assistant that gets things done.\n\nI envision a world where everyone has their own personal AI assistant—something like Jarvis from Iron Man. Not just a tool, but a proactive, intelligent presence that knows you, helps you, and works with you. That’s the kind of future I want to help build.\n\nGAIA was founded by me and [Dhruv](https://www.linkedin.com/in/dhruvmaradiya/). As of June 2025, we’re a really small team of under 5 people—building fast, learning fast, and trying to solve one of the hardest and most exciting problems in tech today.\n\nWe’re just getting started, and there’s a lot more to come. I hope you find what we’re building useful, thoughtful, and maybe even a little magical. Thanks for being here.",
    authors: [
      {
        name: "Aryan Randeriya",
        avatar: "https://github.com/aryanranderiya.png",
        role: "Founder & CEO",
        linkedin: "https://www.linkedin.com/in/aryanranderiya/",
        twitter: "https://twitter.com/aryanranderiya",
      },
    ],
  };

  return (
    <div className="flex min-h-screen w-screen justify-center bg-black px-6 py-28">
      <div className="fixed top-0 left-0 z-[0] flex h-screen w-full items-center justify-center opacity-5">
        <Image
          src="/branding/logo.webp"
          alt="GAIA Logo"
          className="scale-110 object-contain grayscale"
          fill
        />
      </div>

      <div className="relative max-w-(--breakpoint-md) space-y-8">
        <Suspense fallback={<div>Loading...</div>}>
          <div className="flex w-full justify-center">
            <Image
              src="/branding/logo.webp"
              alt="GAIA Logo"
              width={80}
              height={80}
            />
          </div>
          <div className="prose max-w-xl prose-zinc dark:prose-invert">
            <ReactMarkdown
              components={{
                h1: ({ children }) => (
                  <h1 className="mb-6 text-center text-3xl font-bold">
                    {children}
                  </h1>
                ),
                h2: ({ children }) => (
                  <h2 className="mt-8 mb-4 text-2xl font-semibold">
                    {children}
                  </h2>
                ),
                h3: ({ children }) => (
                  <h3 className="mt-6 mb-3 text-xl font-semibold">
                    {children}
                  </h3>
                ),
                p: ({ children }) => (
                  <p className="mb-4 text-justify text-lg leading-relaxed font-light text-foreground-600">
                    {children}
                  </p>
                ),
                ul: ({ children }) => (
                  <ul className="mb-4 ml-6 list-disc space-y-2">{children}</ul>
                ),
                li: ({ children }) => (
                  <li className="text-foreground-600">{children}</li>
                ),
                strong: ({ children }) => (
                  <strong className="font-semibold text-foreground">
                    {children}
                  </strong>
                ),
                a: ({ children }) => (
                  <a className="cursor-pointer text-primary hover:underline">
                    {children}
                  </a>
                ),
              }}
            >
              {aboutData.content}
            </ReactMarkdown>
          </div>
        </Suspense>

        <div className="flex items-start">
          <div className="flex items-center -space-x-2">
            {aboutData.authors.map((author: Author) => (
              <AuthorTooltip
                key={author.name}
                author={author}
                avatarSize="md"
                avatarClassName="h-10 w-10 cursor-help border-2 border-background"
              />
            ))}
          </div>
          <div className="ml-4">
            <div className="font-medium">{aboutData.authors[0]?.name}</div>
            <div className="text-sm text-foreground-500">
              — {aboutData.authors[0]?.role}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
