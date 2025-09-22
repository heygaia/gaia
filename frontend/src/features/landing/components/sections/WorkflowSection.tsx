import { Chip } from "@heroui/chip";
import { DotLottieReact } from "@lottiefiles/dotlottie-react";
import Image from "next/image";

import { BentoItem } from "./TodosBentoContent";

export default function WorkflowSection() {
  const triggers = [
    {
      icon: "/images/icons/slack.svg",
      title: "Slack",
      description: "Trigger on Slack mention",
    },
    {
      icon: "/images/icons/googlecalendar.webp",
      title: "Calendar",
      description: "Trigger on calendar event",
    },

    {
      icon: "/images/icons/gmail.svg",
      title: "Gmail",
      description: "Trigger on new email",
    },
  ];

  return (
    <div className="flex w-full max-w-7xl flex-col justify-center p-7">
      <div className="mb-2 text-2xl font-light text-primary">
        Your Daily Life, Automated
      </div>
      <div className="mb-5 text-5xl font-normal">
        Simple workflows to eliminate repetitive tasks
      </div>

      <div className="grid w-full max-w-7xl grid-cols-3 grid-rows-1 justify-between gap-7">
        <BentoItem
          title="Smart Triggers"
          description="Set conditions once, automate actions forever."
        >
          <div className="flex w-full flex-col items-center justify-center gap-3 px-1">
            {triggers.map((trigger, index) => (
              <div
                key={index}
                className={`flex w-full items-center gap-3 rounded-2xl bg-zinc-800 p-3`}
              >
                <Image
                  src={trigger.icon}
                  alt={trigger.title}
                  className="h-8 w-8"
                  width={32}
                  height={32}
                />
                <div className="flex flex-col">
                  <span className="text-base font-medium text-white">
                    {trigger.title}
                  </span>
                  <span className="text-sm text-zinc-300">
                    {trigger.description}
                  </span>
                </div>
              </div>
            ))}
            <Chip color="primary" variant="flat" className="mt-2 text-primary">
              Automatically run workflows on triggers
            </Chip>
          </div>
        </BentoItem>
        <BentoItem
          title="Proactive by Nature"
          description="GAIA acts before you ask, preparing what you need when you need it."
          childrenClassName="p-0!"
        >
          <DotLottieReact
            src="/animations/proactive.lottie"
            // loop
            // autoplay
            speed={0.7}
            playOnHover
          />
        </BentoItem>
        <BentoItem
          title="Seamless Orchestration"
          description="Makes all your apps work together like a single tool, through a unified interface."
        />
      </div>
    </div>
  );
}
