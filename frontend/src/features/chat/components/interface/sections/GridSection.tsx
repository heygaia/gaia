import React from "react";
import UpcomingEventsView from "@/features/calendar/components/UpcomingEventsView";
import { useRouter } from "next/navigation";

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
      <div className="grid h-screen w-full max-w-7xl grid-cols-2 grid-rows-4 gap-4">
        {/* Top-left */}
        <div className="flex items-center justify-center rounded-2xl bg-zinc-800 p-6">
          <div className="text-center">
            <h1 className="text-3xl font-bold text-foreground">DUMMY</h1>
            <p className="mt-2 text-sm text-foreground/60">
              Placeholder content
            </p>
          </div>
        </div>
        {/* Top-right */}
        <div className="row-span-2 flex max-h-[70vh] items-center justify-center rounded-3xl">
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
