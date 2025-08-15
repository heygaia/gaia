import CalendarContent from "@/features/landing/components/sections/new/CalendarContent";
import LargeHeader from "../../shared/LargeHeader";
import SectionLayout from "../../shared/SectionLayout";
import MailAnimationWrapper from "./MailAnimationWrapper";

export default function MailCalendarSection() {
  return (
    <SectionLayout>
      <div className="h-screen w-full max-w-7xl">
        <div className="grid h-full grid-cols-1 gap-8 lg:grid-cols-2 lg:gap-12">
          <div className="flex flex-col">
            <LargeHeader
              chipText="Mail"
              headingText="Inbox on Autopilot"
              subHeadingText="Compose, view, and manage your emails with simple commands. GAIA streamlines your entire workflow."
            />
            <div className="relative mt-8 min-h-0 flex-1">
              <div className="rounded-3xl bg-zinc-900 p-4">
                <MailAnimationWrapper />
              </div>
            </div>
          </div>

          <div className="flex flex-col">
            <LargeHeader
              chipText="Calendar"
              headingText="Calendar, Reimagined."
              subHeadingText="Schedule, update, and manage your calendar just by texting GAIA. Never open your calendar app again."
            />
            <div className="relative mt-8 min-h-0 flex-1">
              <div className="h-full rounded-3xl bg-zinc-900 p-4">
                <CalendarContent />
              </div>
            </div>
          </div>
        </div>
      </div>
    </SectionLayout>
  );
}
