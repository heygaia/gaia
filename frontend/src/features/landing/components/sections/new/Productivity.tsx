import { CalendarDemo } from "@/features/calendar/components/Calendar";
import { Tab, Tabs } from "@heroui/react";
import { useState } from "react";
import LargeHeader from "../../shared/LargeHeader";
import GoalsStepsContent from "./GoalsStepsContent";
import MailAnimationWrapper from "./MailAnimationWrapper";
import TodosBentoContent from "./TodosBentoContent";

export default function Productivity() {
  const [selectedTab, setSelectedTab] = useState("email");

  return (
    <div className="relative flex h-screen min-h-screen flex-col items-center justify-start overflow-hidden pt-20">
      {/* <div
        className="absolute inset-0 z-0"
        style={{
          background:
            "radial-gradient(125% 125% at 50% 90%, #00000000 40%, #ffffff30 100%)",
        }}
      /> */}
      <div className="relative z-[1] flex w-full max-w-7xl flex-col items-center justify-center p-7">
        <LargeHeader
          centered
          headingText="Productivity, Supercharged."
          subHeadingText="Streamline your workflow with intelligent email management, smart calendar scheduling, goal tracking, and task organization - all through simple conversations."
        />
        <Tabs
          // variant="underlined"
          variant="light"
          size="lg"
          color="primary"
          radius="sm"
          selectedKey={selectedTab}
          onSelectionChange={(key) => setSelectedTab(key as string)}
          className="mt-6 flex w-full justify-center"
        >
          <Tab key="email" title="Email">
            <div className="flex w-screen max-w-6xl items-center justify-center rounded-3xl bg-zinc-900 p-4">
              <MailAnimationWrapper />
            </div>
          </Tab>
          <Tab key="calendar" title="Calendar">
            <div className="flex w-screen max-w-6xl items-center justify-center rounded-3xl bg-zinc-900 p-4">
              <CalendarDemo />
            </div>
          </Tab>
          <Tab key="goals" title="Goals">
            <div className="flex w-screen max-w-6xl items-center justify-center rounded-3xl bg-zinc-900 p-4">
              <GoalsStepsContent />
            </div>
          </Tab>
          <Tab key="todos" title="Todos">
            <div className="flex w-screen max-w-6xl items-center justify-center">
              <TodosBentoContent />
            </div>
          </Tab>
        </Tabs>
      </div>
    </div>
  );
}
