import { Button } from "@heroui/button";
import { Tooltip } from "@heroui/react";
import { Play, RotateCcw } from "lucide-react";

import { WorkflowSquare03Icon } from "@/components";

interface WorkflowHeaderProps {
  isRunning: boolean;
  onGenerateWorkflow?: () => void;
  onRunWorkflow: () => void;
}

export default function WorkflowHeader({
  isRunning,
  onGenerateWorkflow,
  onRunWorkflow,
}: WorkflowHeaderProps) {
  return (
    <div className="flex items-center justify-between">
      <div className="flex items-center gap-2">
        <WorkflowSquare03Icon className="h-5 w-5 text-zinc-400" />
        <h3 className="text-base font-medium text-zinc-100">Workflow</h3>
      </div>
      <div className="flex items-center gap-2">
        <Tooltip content="Regnerate Workflow" color="foreground">
          <Button
            color="default"
            variant="flat"
            size="sm"
            onPress={onGenerateWorkflow}
            startContent={<RotateCcw className="h-4 w-4" />}
            isIconOnly
          />
        </Tooltip>

        <Button
          color="success"
          variant="flat"
          size="sm"
          isLoading={isRunning}
          onPress={onRunWorkflow}
          startContent={!isRunning ? <Play className="h-4 w-4" /> : undefined}
          className="bg-green-500/20 text-green-400 hover:bg-green-500/30"
        >
          {isRunning ? "Running..." : "Run Workflow"}
        </Button>
      </div>
    </div>
  );
}
