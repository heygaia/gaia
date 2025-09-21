import Image from "next/image";

import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui";
import { useUser } from "@/features/auth/hooks/useUser";
import SelectedToolIndicator from "@/features/chat/components/composer/SelectedToolIndicator";
import SelectedWorkflowIndicator from "@/features/chat/components/composer/SelectedWorkflowIndicator";
import { ChatBubbleUserProps } from "@/types/features/chatBubbleTypes";
import { parseDate } from "@/utils/date/dateUtils";

import ChatBubbleFilePreview from "./ChatBubbleFilePreview";

export default function ChatBubbleUser({
  text,
  date,
  message_id,
  fileData = [],
  selectedTool,
  toolCategory,
  selectedWorkflow,
}: ChatBubbleUserProps) {
  const hasContent =
    !!text || fileData.length > 0 || !!selectedTool || !!selectedWorkflow;

  const user = useUser();

  if (!hasContent) return null;

  return (
    <div className="flex w-full items-end justify-end gap-3">
      <div className="chat_bubble_container user group" id={message_id}>
        {fileData.length > 0 && <ChatBubbleFilePreview files={fileData} />}

        {selectedTool && (
          <div className="flex justify-end">
            <SelectedToolIndicator
              toolName={selectedTool}
              toolCategory={toolCategory}
            />
          </div>
        )}

        {selectedWorkflow && (
          <div className="flex justify-end">
            <SelectedWorkflowIndicator workflow={selectedWorkflow} />
          </div>
        )}

        {text?.trim() && (
          <div className="chat_bubble user">
            {!!text && (
              <div className="flex max-w-[30vw] text-wrap whitespace-pre-wrap select-text">
                {text}
              </div>
            )}
          </div>
        )}

        <div className="flex justify-end opacity-0 transition-all group-hover:opacity-100">
          {date && (
            <span className="text-opacity-45 flex flex-col pt-[2px] text-xs text-white select-text">
              {parseDate(date)}
            </span>
          )}
        </div>
      </div>
      <div className="sticky -bottom-3 min-w-[40px]">
        <Avatar className="relative bottom-4 rounded-full bg-black">
          <AvatarImage src={user?.profilePicture} alt="User Avatar" />
          <AvatarFallback>
            <Image
              src={"/images/avatars/default.webp"}
              width={35}
              height={35}
              alt="Default profile picture"
            />
          </AvatarFallback>
        </Avatar>
      </div>
    </div>
  );
}
