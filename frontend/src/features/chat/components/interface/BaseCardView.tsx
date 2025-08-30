import { Skeleton } from "@heroui/react";
import React from "react";

interface BaseCardViewProps {
  title: string;
  icon: React.ReactNode;
  isLoading: boolean;
  error?: string | null;
  isEmpty?: boolean;
  emptyMessage?: string;
  errorMessage?: string;
  children: React.ReactNode;
  className?: string;
}

const BaseCardView: React.FC<BaseCardViewProps> = ({
  title,
  icon,
  isLoading,
  error,
  isEmpty = false,
  emptyMessage = "No data available",
  errorMessage = "Failed to load data",
  children,
  className = "",
}) => {
  const containerClassName = `flex h-full min-h-[40vh] max-h-[40vh] w-full flex-col ${className} rounded-3xl`;

  return (
    <div className={containerClassName}>
      <div className="flex-shrink-0 px-4 py-3">
        <div className="flex items-center gap-2">
          {icon}
          <h3 className="font-medium text-white">{title}</h3>
        </div>
      </div>

      <div className="h-full flex-1 px-4 pb-4">
        <Skeleton
          className="w-full rounded-2xl"
          isLoaded={!isLoading}
          classNames={{ base: "h-full", content: "h-full" }}
        >
          <div className="h-full max-h-[40vh] min-h-[40vh] w-full overflow-y-auto rounded-2xl bg-[#141414]">
            {error || isEmpty ? (
              <div className="flex h-full flex-col items-center justify-center">
                <div className="mb-2 opacity-50">{icon}</div>
                <p className="text-sm text-foreground/60">
                  {error ? errorMessage : emptyMessage}
                </p>
              </div>
            ) : (
              children
            )}
          </div>
        </Skeleton>
      </div>
    </div>
  );
};

export default BaseCardView;
