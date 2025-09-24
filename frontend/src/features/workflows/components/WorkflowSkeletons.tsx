import { Skeleton } from "@/components/ui/shadcn/skeleton";

import BaseWorkflowCard from "./shared/BaseWorkflowCard";

export const WorkflowCardSkeleton = () => {
  return (
    <Skeleton>
      <BaseWorkflowCard title="" description="" />
    </Skeleton>
  );
};

export const WorkflowStepSkeleton = () => {
  return (
    <div className="flex items-start gap-3 rounded-lg border border-zinc-800 p-3">
      <Skeleton className="h-8 w-8 flex-shrink-0 rounded-full" />
      <div className="flex-1 space-y-2">
        <Skeleton className="h-5 w-3/4" />
        <Skeleton className="h-4 w-full" />
        <Skeleton className="h-4 w-1/2" />
      </div>
    </div>
  );
};

export const WorkflowDetailSkeleton = () => {
  return (
    <div className="space-y-6">
      {/* Header skeleton */}
      <div className="space-y-3">
        <Skeleton className="h-8 w-1/2" />
        <Skeleton className="h-4 w-full" />
        <Skeleton className="h-4 w-3/4" />
      </div>

      {/* Trigger info skeleton */}
      <div className="flex items-center gap-2">
        <Skeleton className="h-6 w-6 rounded-full" />
        <Skeleton className="h-5 w-32" />
      </div>

      {/* Steps skeleton */}
      <div className="space-y-3">
        <Skeleton className="h-6 w-40" />
        <WorkflowStepSkeleton />
        <WorkflowStepSkeleton />
        <WorkflowStepSkeleton />
      </div>
    </div>
  );
};

export const WorkflowListSkeleton = () => {
  return (
    <div className="grid max-w-7xl grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
      {Array.from({ length: 4 }).map((_, i) => (
        <WorkflowCardSkeleton key={i} />
      ))}
    </div>
  );
};
