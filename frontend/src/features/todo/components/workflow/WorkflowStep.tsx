import { Chip } from "@heroui/chip";
import { Tooltip } from "@heroui/tooltip";

import { formatToolName } from "@/features/chat/utils/chatUtils";
import { getToolCategoryIcon } from "@/features/chat/utils/toolIcons";

interface WorkflowStepProps {
  step: {
    id: string;
    title: string;
    description: string;
    tool_name: string;
    tool_category: string;
  };
  index: number;
}

export default function WorkflowStep({ step, index }: WorkflowStepProps) {
  return (
    <div className="relative flex items-start gap-4">
      {/* Timeline dot with number */}
      <div className="relative z-10 flex h-7 w-7 flex-shrink-0 items-center justify-center rounded-full border-2 border-primary/60 bg-zinc-800 shadow-lg">
        <span className="text-xs font-semibold text-primary">{index + 1}</span>
      </div>

      {/* Step content */}
      <div className="flex-1 space-y-3">
        <div className="flex items-center gap-2">
          <Tooltip content="Tool Name" size="sm" color="foreground">
            <Chip
              radius="sm"
              className="space-x-1 pl-2 text-xs"
              startContent={getToolCategoryIcon(step.tool_category, {
                size: 10,
                width: 10,
                height: 10,
              })}
            >
              {formatToolName(step.tool_name)}
            </Chip>
          </Tooltip>
          <Tooltip content="Tool Category" size="sm" color="foreground">
            <Chip
              size="sm"
              variant="flat"
              color="primary"
              className="text-primary capitalize"
            >
              {step.tool_category.replace("_", " ")}
            </Chip>
          </Tooltip>
        </div>

        <div className="flex flex-col items-start">
          <h5 className="text-sm leading-relaxed font-medium text-zinc-100">
            {step.title}
          </h5>

          <p className="text-xs leading-relaxed text-zinc-400">
            {step.description}
          </p>
        </div>
      </div>
    </div>
  );
}
