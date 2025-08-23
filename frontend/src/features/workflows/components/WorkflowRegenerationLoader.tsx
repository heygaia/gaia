import CustomSpinner from "@/components/ui/shadcn/spinner";

interface WorkflowRegenerationLoaderProps {
  reason?: string;
  workflowTitle?: string;
}

export default function WorkflowRegenerationLoader({
  reason,
  workflowTitle,
}: WorkflowRegenerationLoaderProps) {
  return (
    <div className="space-y-6">
      <div className="flex flex-col items-center justify-center py-8">
        <div className="text-center">
          {/* Simple Spinner */}
          <div className="mb-6">
            <CustomSpinner variant="logo" />
          </div>

          {/* Loading Text */}
          <div>
            <h3 className="text-lg font-medium text-zinc-100">
              Regenerating Workflow Steps
            </h3>
            <p className="mt-2 text-sm text-zinc-400">
              {reason && workflowTitle
                ? `${reason} for: "${workflowTitle}"`
                : "AI is creating new workflow steps..."}
            </p>
          </div>

          {/* Additional Status Text */}
          <div className="mt-4 text-xs text-zinc-500">
            ✨ This may take a few moments...
          </div>
        </div>
      </div>
    </div>
  );
}
