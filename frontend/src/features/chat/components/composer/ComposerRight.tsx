import { Button } from "@heroui/button";
import { Tooltip } from "@heroui/tooltip";
import { ArrowUp } from "lucide-react";

import { useLoading } from "@/features/chat/hooks/useLoading";

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
  const { isLoading } = useLoading();
  const hasText = searchbarText.trim().length > 0;
  const hasSelectedTool = selectedTool !== null && selectedTool !== undefined;
  const isDisabled = isLoading || (!hasText && !hasSelectedTool);

  const getTooltipContent = () => {
    if (hasSelectedTool && !hasText) {
      // Format tool name to be more readable
      const formattedToolName = selectedTool
        ?.split("_")
        .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
        .join(" ");
      return `Send with ${formattedToolName}`;
    }
    return "Send message";
  };

  return (
    <div className="ml-2 flex items-center gap-1">
      <Tooltip
        content={getTooltipContent()}
        placement="right"
        color="primary"
        showArrow
      >
        <Button
          isIconOnly
          aria-label="Send message"
          className={`${isLoading && "cursor-wait"} h-9 min-h-9 w-9 max-w-9 min-w-9`}
          color={hasText || hasSelectedTool ? "primary" : "default"}
          disabled={isDisabled}
          isLoading={isLoading}
          radius="full"
          type="submit"
          onPress={() => handleFormSubmit()}
        >
          <ArrowUp color={hasText || hasSelectedTool ? "black" : "gray"} />
        </Button>
      </Tooltip>
    </div>
  );
}
