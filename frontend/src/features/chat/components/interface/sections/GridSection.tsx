import { useRouter } from "next/navigation";
import React from "react";

import UpcomingEventsView from "@/features/calendar/components/UpcomingEventsView";
import UnreadEmailsView from "@/features/mail/components/UnreadEmailsView";

interface GridSectionProps {
  dummySectionRef: React.RefObject<HTMLDivElement | null>;
}

export const GridSection: React.FC<GridSectionProps> = ({
  dummySectionRef,
}) => {
  const router = useRouter();
  return (
    <div
      ref={dummySectionRef}
      className="relative flex h-fit snap-start items-center justify-center p-4 pt-24"
    >
      <div className="grid h-screen max-h-[80vh] w-full max-w-7xl grid-cols-2 grid-rows-4 gap-4">
        <div className="row-span-2 flex items-center justify-center rounded-3xl">
          <UnreadEmailsView />
        </div>
        {/* Top-right */}
        <div className="row-span-2 flex items-center justify-center rounded-3xl">
          <UpcomingEventsView
            onEventClick={(event) => {
              router.push("/calendar");
            }}
          />
        </div>
        {/* <div className="col-span-2 rounded-lg bg-[#141414] p-4">
          <div className="h-full"></div>
        </div> */}
      </div>
    </div>
  );
};
