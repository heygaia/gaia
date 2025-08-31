import React from "react";

import CardStackContainer from "@/features/chat/components/interface/CardStackContainer";

interface CardStackSectionProps {
  cardStackSectionRef: React.RefObject<HTMLDivElement | null>;
}

export const CardStackSection: React.FC<CardStackSectionProps> = ({
  cardStackSectionRef,
}) => {
  return (
    <div
      ref={cardStackSectionRef}
      className="relative flex h-screen min-h-screen snap-start items-center justify-center p-4"
    >
      <div className="w-full max-w-(--breakpoint-xl)">
        <CardStackContainer />
      </div>
    </div>
  );
};
