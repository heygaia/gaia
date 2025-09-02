import { Chip } from "@heroui/chip";
import Image from "next/image"

import OrbitingCircles from "@/components/ui/magic-ui/orbiting-circles";

import { BentoItem } from "./new/TodosBentoContent";

export default function WorkflowSection() {
  const triggers = [

    {
      icon: "/icons/slack.svg",
      title: "Slack",
      description: "Trigger on Slack mention"
    },
    {
      icon: "/icons/googlecalendar.webp",
      title: "Calendar",
      description: "Trigger on calendar event"
    },

    {
      icon: "/icons/gmail.svg",
      title: "Gmail",
      description: "Trigger on new email"
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
          <div className="flex flex-col gap-3 w-full justify-center items-center px-1">
            {triggers.map((trigger, index) => (
              <div
                key={index}
                className={`flex items-center gap-3 bg-zinc-800 rounded-2xl p-3 w-full `}
              >
                <Image
                  src={trigger.icon}
                  alt={trigger.title}
                  className="w-8 h-8"
                  width={32}
                  height={32}
                />
                <div className="flex flex-col">
                  <span className="text-white text-base font-medium">{trigger.title}</span>
                  <span className="text-zinc-300 text-sm">{trigger.description}</span>
                </div>
              </div>
            ))}
            <Chip color="primary" variant="flat" className="text-primary mt-2">
              Automatically run workflows on triggers
            </Chip>
          </div>
        </BentoItem>
        <BentoItem
          title="Proactive by Nature"
          description="GAIA acts before you ask, preparing what you need when you need it."
        >
          <OrbitingCircles />
        </BentoItem>
        <BentoItem
          title="Seamless Orchestration"
          description="Makes all your apps work together like a single tool, through a unified interface."
        />
      </div>
    </div>
  );
}
