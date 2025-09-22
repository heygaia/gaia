import {
  BellRing,
  FileText,
  FolderOpen,
  Mail,
  MessageSquare,
  PenLineIcon,
  PenSquare,
  Reply,
  Search,
  Zap,
} from "lucide-react";
import Image from "next/image";
import { useCallback, useEffect, useState } from "react";

import { Card } from "@/components/ui/shadcn/card";

import { cn } from "../../../../lib/utils";
import LargeHeader from "../shared/LargeHeader";

const images = [
  {
    id: "3",
    src: "/landing/mail/email3.webp",
    alt: "mail Screenshot 3",
  },
  {
    id: "2",
    src: "/landing/mail/email2.webp",
    alt: "mail Screenshot 2",
  },
  {
    id: "4",
    src: "/landing/mail/email4.webp",
    alt: "mail Screenshot 4",
  },
  {
    id: "1",
    src: "/landing/mail/email1.webp",
    alt: "mail Screenshot 1",
  },
];

const bentoCards = [
  {
    icon: <PenLineIcon className="h-5 w-5" />,
    title: "Never write the same email twice",
    description:
      "Easily personalize and send similar emails to different people without accidentally sending the exact same message twice.",
  },
  {
    icon: <BellRing className="h-5 w-5" />,
    title: "Never miss important emails",
    description:
      "Our smart system highlights important messages so they don't get lost in your busy inbox.",
  },
  {
    icon: <MessageSquare className="h-5 w-5" />,
    title: "chat to send emails",
    description:
      "Just chat with our AI assistant to create and send emails - as simple as texting a friend.",
  },
  {
    icon: <Reply className="h-5 w-5" />,
    title: "Smart Replies",
    description:
      "AI-powered suggestions for quick responses to common emails, saving you time and effort with just one click.",
  },
  {
    icon: <FileText className="h-5 w-5" />,
    title: "Summarisation",
    description:
      "Turn long email threads into short, clear summaries with just one click.",
  },
  {
    icon: <Zap className="h-5 w-5" />,
    title: "Built for speed",
    description:
      "Work faster with shortcuts, quick replies, and a lightning-fast platform designed to save you time.",
  },
  {
    icon: <PenSquare className="h-5 w-5" />,
    title: "Write emails with AI",
    description:
      "Create perfect emails in seconds with our AI that learns your style and helps you write better messages.",
  },
  {
    icon: <FolderOpen className="h-5 w-5" />,
    title: "Organize your inbox effortlessly",
    description:
      "Smart filters and automatic categorization help you maintain a clean, organized inbox without any manual effort.",
  },
  {
    icon: <Search className="h-5 w-5" />,
    title: "Find any email address",
    description:
      "Quickly find anyone's email address with our built-in search tool - no more hunting for contact details.",
  },
  {
    icon: <Mail className="h-5 w-5" />,
    title: "All your emails in one place",
    description:
      "Manage all your email accounts in one simple, clean interface that makes email easy.",
  },
];

export default function MailSection() {
  const [activeImage, setActiveImage] = useState(images[0].id);

  // Auto-rotate images
  const nextImage = useCallback(() => {
    setActiveImage((prevId) => {
      const currentIndex = images.findIndex((img) => img.id === prevId);
      const nextIndex = (currentIndex + 1) % images.length;
      return images[nextIndex].id;
    });
  }, []);

  useEffect(() => {
    const timer = setInterval(nextImage, 4000);
    return () => clearInterval(timer);
  }, [nextImage]);

  return (
    <div className="flex w-screen flex-col items-center justify-center">
      <div className="flex w-screen max-w-(--breakpoint-xl) flex-col items-center space-y-10">
        <LargeHeader
          headingText="The Future of Mail"
          chipText="Mail"
          chipText2="Coming Soon"
          // subHeadingText="An AI-native inbox that writes, replies, and thinks for you."
          subHeadingText="An intelligent inbox assistant that helps you write better emails, reply instantly, surface important messages, and stay organized — all in one place."
        />

        <div className="mt-10 grid w-screen max-w-(--breakpoint-xl) grid-cols-1 gap-2 p-3 sm:gap-6 sm:p-0 md:grid-cols-2 lg:grid-cols-5">
          {bentoCards.map((card, index) => (
            <BentoCard
              key={index}
              icon={card.icon}
              title={card.title}
              description={card.description}
            />
          ))}
        </div>

        <div className="flex justify-center">
          <div className="relative w-full max-w-(--breakpoint-xl)">
            <div className="relative aspect-video w-screen max-w-(--breakpoint-xl) overflow-hidden rounded-xl shadow-[0_4px_150px_#00bbff90] sm:min-h-[70vh]">
              {images.map((image) => (
                <div
                  key={image.id}
                  className={cn(
                    "absolute inset-0 h-full w-full cursor-pointer overflow-hidden rounded-xl transition-opacity duration-500 ease-in-out",
                    activeImage === image.id ? "opacity-100" : "opacity-0",
                  )}
                  onClick={nextImage}
                >
                  <Image
                    src={image.src}
                    alt={image.alt}
                    fill
                    className="w-full rounded-xl object-cover"
                  />
                </div>
              ))}
            </div>
          </div>
        </div>

        <div className="mt-4 flex justify-center space-x-2">
          {images.map((image) => (
            <button
              key={image.id}
              onClick={() => setActiveImage(image.id)}
              className={cn(
                "max-h-[10px] min-h-[10px] max-w-[10px] min-w-[10px] rounded-full transition",
                activeImage === image.id
                  ? "bg-primary"
                  : "bg-gray-600 hover:bg-gray-400",
              )}
              aria-label={`Go to slide ${image.id}`}
            />
          ))}
        </div>
      </div>
    </div>
  );
}

function BentoCard({
  icon,
  title,
  description,
}: {
  icon: React.ReactNode;
  title: string;
  description: string;
}) {
  return (
    <Card className="flex h-full flex-col rounded-2xl border-none bg-linear-to-br from-primary/20 to-black p-5 outline-hidden">
      <div className="mb-2 text-primary">{icon}</div>
      <h3 className="relative z-1 text-[1rem] font-semibold text-white">
        {title}
      </h3>
      <p className="relative z-1 grow text-sm text-white/80">{description}</p>
    </Card>
  );
}
