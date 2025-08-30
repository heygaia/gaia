import { CheckmarkCircle02Icon } from "@/components/shared/icons";

interface WorkflowRegenerationSuccessProps {
  stepsCount: number;
  onComplete?: () => void;
}

export default function WorkflowRegenerationSuccess({
  stepsCount,
  onComplete,
}: WorkflowRegenerationSuccessProps) {
  // Auto complete after 2 seconds
  setTimeout(() => {
    onComplete?.();
  }, 2000);

  return (
    <div className="space-y-4">
      <div className="flex flex-col items-center justify-center py-4">
        <div className="text-center">
          {/* Success Icon */}
          <div className="mb-4">
            <CheckmarkCircle02Icon className="mx-auto h-16 w-16 text-success" />
          </div>

          {/* Success Text */}
          <div>
            <h3 className="text-lg font-medium text-success">
              Steps Regenerated!
            </h3>
            <p className="text-sm text-zinc-400">
              {stepsCount} new steps generated successfully
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
