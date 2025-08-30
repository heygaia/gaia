import ShinyText from "@/components/ui/shadcn/shimmering-chip";
import { getToolCategoryIcon } from "@/features/chat/utils/toolIcons";

interface WorkflowGeneratingShimmerProps {
  title: string;
  description?: string;
  estimatedSteps?: number;
}

export const WorkflowGeneratingShimmer = ({
  title,
  description,
  estimatedSteps = 3,
}: WorkflowGeneratingShimmerProps) => {
  // Common tool categories for shimmer effect
  const shimmerCategories = ["productivity", "search", "documents"];

  return (
    <div className="relative flex aspect-square cursor-pointer flex-col rounded-2xl border-1 border-primary/20 bg-gradient-to-br from-primary/5 to-primary/10 p-4 transition duration-300">
      {/* Generating indicator */}
      <div className="absolute top-4 right-4">
        <div className="flex items-center gap-2">
          <div className="h-2 w-2 animate-ping rounded-full bg-primary"></div>
          <span className="text-xs font-medium text-primary">Generating</span>
        </div>
      </div>

      {/* Tool icons with shimmer */}
      <div className="flex items-center gap-2">
        {shimmerCategories
          .slice(0, Math.min(3, estimatedSteps))
          .map((category, index) => (
            <div
              key={index}
              className="flex h-[40px] w-[40px] animate-pulse items-center justify-center rounded-lg bg-zinc-700/50"
              style={{ animationDelay: `${index * 200}ms` }}
            >
              {getToolCategoryIcon(category, {
                size: 16,
                width: 16,
                height: 16,
              })}
            </div>
          ))}

        {estimatedSteps > 3 && (
          <div className="flex h-[40px] w-[40px] animate-pulse items-center justify-center rounded-lg bg-zinc-700/50">
            <span className="text-xs font-bold">+{estimatedSteps - 3}</span>
          </div>
        )}
      </div>

      {/* Title with shimmer effect */}
      <div className="mt-4">
        <ShinyText text={title} speed={3} className="text-lg font-medium" />
      </div>

      {/* Description */}
      {description && (
        <div className="mt-2 flex-1 text-sm text-foreground-500">
          {description}
        </div>
      )}

      {/* Shimmer steps preview */}
      <div className="mt-4 space-y-2">
        <div className="text-xs text-foreground-400">Generating steps...</div>
        <div className="space-y-1">
          {Array.from({ length: 3 }).map((_, i) => (
            <div
              key={i}
              className="h-2 animate-pulse rounded-full bg-gradient-to-r from-zinc-700 to-zinc-600"
              style={{
                width: `${60 + i * 15}%`,
                animationDelay: `${i * 200}ms`,
              }}
            />
          ))}
        </div>
      </div>

      {/* Bottom status */}
      <div className="mt-4 flex w-full items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="h-4 w-4 animate-spin rounded-full border-2 border-primary border-t-transparent"></div>
          <span className="text-xs text-primary">AI Working</span>
        </div>
        <div className="rounded-full bg-primary/20 px-2 py-1 text-xs text-primary">
          Draft
        </div>
      </div>
    </div>
  );
};
