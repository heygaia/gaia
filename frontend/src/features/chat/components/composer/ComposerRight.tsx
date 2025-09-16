import { Button } from "@heroui/button";
import { Kbd } from "@heroui/react";
import { Tooltip } from "@heroui/tooltip";
import { ArrowUp, Square } from "lucide-react";

import { useLoading } from "@/features/chat/hooks/useLoading";
import { useWorkflowSelection } from "@/features/chat/hooks/useWorkflowSelection";

interface RightSideProps {
  handleFormSubmit: (e?: React.FormEvent<HTMLFormElement>) => void;
  searchbarText: string;
  selectedTool?: string | null;
}

export default function RightSide({
  handleFormSubmit,
  searchbarText,
  selectedTool,
}: RightSideProps) {
  const { isLoading, stopStream } = useLoading();
  const { selectedWorkflow } = useWorkflowSelection();
  const hasText = searchbarText.trim().length > 0;
  const hasSelectedTool = selectedTool != null;
  const hasSelectedWorkflow = selectedWorkflow != null;
  const isDisabled =
    isLoading || (!hasText && !hasSelectedTool && !hasSelectedWorkflow);

  const getTooltipContent = () => {
    if (isLoading) return "Stop generation";

    if (hasSelectedWorkflow && !hasText && !hasSelectedTool) {
      return `Send with ${selectedWorkflow?.title}`;
    }

    if (hasSelectedTool && !hasText) {
      // Format tool name to be more readable
      const formattedToolName = selectedTool
        ?.split("_")
        .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
        .join(" ");
      return `Send with ${formattedToolName}`;
    }

    if (!hasText && !hasSelectedTool && !hasSelectedWorkflow) {
      return "Message requires text";
    }

    return (
      <div className="flex items-center gap-2">
        Send Message
        <Kbd className="text-zinc-400" keys={["enter"]}></Kbd>
      </div>
    );
  };

  const handleButtonPress = () => {
    if (isLoading) {
      stopStream();
    } else {
      handleFormSubmit();
    }
  };

  return (
    <div className="ml-2 flex items-center gap-1">
      <Tooltip content={getTooltipContent()} placement="right" showArrow>
        <Button
          isIconOnly
          aria-label={isLoading ? "Stop generation" : "Send message"}
          className={`h-9 min-h-9 w-9 max-w-9 min-w-9 ${isLoading ? "cursor-pointer" : ""}`}
          color={
            isLoading
              ? "default"
              : hasText || hasSelectedTool || hasSelectedWorkflow
                ? "primary"
                : "default"
          }
          disabled={!isLoading && isDisabled}
          radius="full"
          type="submit"
          onPress={handleButtonPress}
        >
          {isLoading ? (
            <Square color="lightgray" width={17} height={17} fill="lightgray" />
          ) : (
            <ArrowUp
              color={
                hasText || hasSelectedTool || hasSelectedWorkflow
                  ? "black"
                  : "gray"
              }
            />
          )}
        </Button>
      </Tooltip>
    </div>
  );
}
