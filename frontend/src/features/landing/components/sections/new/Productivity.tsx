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
    <>
      <div className="gap- flex h-screen min-h-screen flex-col items-center justify-start">
        <div className="flex w-full max-w-7xl flex-col justify-center p-7">
          <LargeHeader
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
            className="mt-6 w-full"
          >
            <Tab key="email" title="Email">
              <div className="flex items-center justify-center rounded-3xl bg-zinc-900 p-4">
                <MailAnimationWrapper />
              </div>
            </Tab>
            <Tab key="calendar" title="Calendar">
              <div className="flex items-center justify-center rounded-3xl bg-zinc-900 p-4">
                <CalendarDemo />
              </div>
            </Tab>
            <Tab key="goals" title="Goals">
              <div className="flex items-center justify-center rounded-3xl bg-zinc-900 p-4">
                <GoalsStepsContent />
              </div>
            </Tab>
            <Tab key="todos" title="Todos">
              <div className="flex items-center justify-center">
                <TodosBentoContent />
              </div>
            </Tab>
          </Tabs>
        </div>
      </div>
    </>
  );
}
