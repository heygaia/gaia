import { AiBrain01Icon } from "@/components";

import MemoryGraphDemo from "../demo/MemoryGraphDemo";
import { SimpleChatBubbleUser } from "../demo/SimpleChatBubbles";
import { BentoItem } from "./TodosBentoContent";

export default function Personalised() {
  const personalInfo = [
    "You work as a Senior Software Engineer at Google",
    "Your girlfriend is Emma Rodriguez, and you've been dating for 2 years",
    "You have a 2-year-old Golden Retriever named Buster",
  ];

  return (
    <div className="flex flex-col items-center justify-center gap-10">
      <div className="flex w-full max-w-7xl flex-col justify-center p-7">
        <div className="mb-2 text-center text-2xl font-light text-primary">
          Truly Personalised
        </div>
        <div className="text-center text-5xl font-normal">
          Finally, AI that feels like it's made for you
        </div>
        <div className="grid w-full max-w-7xl grid-cols-3 grid-rows-1 justify-between gap-7 py-10">
          <BentoItem
            title="Recall Everything Instantly"
            description="GAIA remembers every detail you mention in a conversation"
          >
            <div className="flex w-full flex-col gap-2">
              <SimpleChatBubbleUser className2="mb-2">
                What do you know about me?
              </SimpleChatBubbleUser>
              {personalInfo.map((info, index) => (
                <div
                  key={index}
                  className="mr-7 flex gap-1 rounded-2xl bg-zinc-700 px-4 py-2"
                >
                  <AiBrain01Icon className="relative top-0.5 text-zinc-400" />

                  <div className="w-full">{info}</div>
                </div>
              ))}
            </div>
          </BentoItem>
          <BentoItem title="lorem ipsum" description="lorem ipsum" />

          <BentoItem
            title="Build a Knowledge Graph"
            description="Builds intelligent bridges between your scattered memories"
            childrenClassName="p-0 overflow-hidden"
          >
            <MemoryGraphDemo />
          </BentoItem>
        </div>
      </div>
    </div>
  );
}
