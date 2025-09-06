"use client";

import { Accordion, AccordionItem } from "@heroui/accordion";

export function FAQAccordion() {
  const faqItems = [
    {
      question: "What is Gaia and how does it work?",
      content:
        "Gaia is an advanced general-purpose AI assistant that revolutionizes how you manage your daily life. It seamlessly integrates with your existing workflows to provide intelligent time management, automated event scheduling, smart email organization, and proactive task prioritization. Using cutting-edge AI technology, Gaia learns your preferences and habits to offer personalized recommendations that help you stay productive and organized.",
    },
    {
      question: "How do I create an account?",
      content:
        "Getting started with Gaia is simple and takes just a few minutes. Click on the 'Sign Up' button located in the top navigation or on our pricing page. You'll be guided through a streamlined registration process where you'll provide basic information like your name, email, and create a secure password. Once registered, you can immediately start connecting your calendars, email accounts, and other productivity tools to begin experiencing Gaia's powerful features.",
    },
    {
      question: "What features does Gaia offer?",
      content:
        "Gaia provides a comprehensive suite of productivity features including intelligent task management with priority scoring, automated event scheduling that finds optimal meeting times, seamless email integration with smart filtering and response suggestions, goal tracking with progress analytics, calendar optimization, reminder systems, and workflow automation. Our AI continuously learns from your behavior to provide increasingly personalized assistance that adapts to your unique working style and preferences.",
    },
    {
      question: "How do I contact support if I have an issue?",
      content:
        "Our dedicated support team is here to help you succeed with Gaia. You can reach us through multiple channels: visit our 'Contact Us' page for instant chat support during business hours, email us directly at support@gaia-ai.com for detailed inquiries, or browse our comprehensive help documentation and video tutorials. We typically respond to emails within 24 hours and offer priority support for premium subscribers.",
    },
  ];

  return (
    <div className="flex h-fit w-full items-center justify-center py-20">
      <div className="w-screen max-w-7xl p-8">
        <div className="mb-10 flex w-full flex-col items-start justify-center gap-3">
          <span className="text-4xl font-medium">
            Frequently asked questions
          </span>
        </div>

        <Accordion
          variant="light"
          className="cursor-pointer p-0!"
          itemClasses={{ titleWrapper: "cursor-pointer" }}
        >
          {faqItems.map((item, index) => (
            <AccordionItem
              key={index}
              aria-label={item.question}
              title={item.question}
              classNames={{
                heading: "font-normal",
                title: "text-2xl",
                content:
                  "text-xl max-w-[50%] text-foreground-500 font-light mb-6",
              }}
            >
              <span className="select-text">{item.content}</span>
            </AccordionItem>
          ))}
        </Accordion>
      </div>
    </div>
  );
}
