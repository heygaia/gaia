// ChatBubbleBot.tsx
import { useCallback, useMemo, useRef } from "react";

import { SystemPurpose } from "@/features/chat/api/chatApi";
import ChatBubble_Actions from "@/features/chat/components/bubbles/actions/ChatBubble_Actions";
import ChatBubble_Actions_Image from "@/features/chat/components/bubbles/actions/ChatBubble_Actions_Image";
import MemoryIndicator from "@/features/chat/components/memory/MemoryIndicator";
import { ChatBubbleBotProps } from "@/types/features/chatBubbleTypes";
import { parseDate } from "@/utils/date/dateUtils";

import ImageBubble from "./ImageBubble";
import TextBubble from "./TextBubble";

export default function ChatBubbleBot(props: ChatBubbleBotProps) {
  const {
    text,
    loading = false,
    message_id,
    pinned,
    image_data,
    date,
    memory_data,
    onOpenMemoryModal,
    isConvoSystemGenerated,
    systemPurpose,
  } = props;

  const actionsRef = useRef<HTMLDivElement>(null);

  const handleMouseOver = useCallback(() => {
    if (actionsRef.current) {
      actionsRef.current.style.opacity = "1";
      actionsRef.current.style.visibility = "visible";
    }
  }, []);

  const handleMouseOut = useCallback(() => {
    if (actionsRef.current) {
      actionsRef.current.style.opacity = "0";
      actionsRef.current.style.visibility = "hidden";
    }
  }, []);

  const renderedComponent = useMemo(() => {
    if (image_data) return <ImageBubble {...props} />;

    return <TextBubble {...props} />;
  }, [image_data, props]);

  return (
    (loading ||
      image_data ||
      !!text ||
      (isConvoSystemGenerated &&
        systemPurpose === SystemPurpose.EMAIL_PROCESSING)) && (
      <div
        id={message_id}
        onMouseOver={handleMouseOver}
        onMouseOut={handleMouseOut}
      >
        <div className="chatbubblebot_parent">
          <div className="flex w-full flex-col gap-2">
            {memory_data && onOpenMemoryModal && (
              <MemoryIndicator
                memoryData={memory_data}
                onOpenModal={onOpenMemoryModal}
              />
            )}
            <div className="chat_bubble_container">{renderedComponent}</div>
          </div>
        </div>

        {!loading && (
          <div
            ref={actionsRef}
            className="absolute flex flex-col transition-all"
            style={{ opacity: 0, visibility: "hidden" }}
          >
            {date && (
              <span className="text-opacity-40 flex flex-col p-1 text-xs text-white select-text">
                {parseDate(date)}
              </span>
            )}

            {image_data ? (
              <ChatBubble_Actions_Image image_data={image_data} />
            ) : (
              <ChatBubble_Actions
                loading={loading}
                message_id={message_id}
                pinned={pinned}
                text={text}
              />
            )}
          </div>
        )}
      </div>
    )
  );
}
