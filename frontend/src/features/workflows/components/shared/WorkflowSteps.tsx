import WorkflowStep from "./WorkflowStep";

interface WorkflowStepsProps {
  steps: Array<{
    id: string;
    title: string;
    description: string;
    tool_name: string;
    tool_category: string;
  }>;
}

export default function WorkflowSteps({ steps }: WorkflowStepsProps) {
  return (
    <div className="py-5">
      <div className="relative">
        {/* Timeline line */}
        <div className="absolute top-4 bottom-8 left-[13px] w-[1px] bg-gradient-to-b from-primary via-primary/80 to-transparent"></div>

        <div className="space-y-8">
          {steps.map((step, index) => (
            <WorkflowStep key={step.id} step={step} index={index} />
          ))}
        </div>
      </div>
    </div>
  );
}
