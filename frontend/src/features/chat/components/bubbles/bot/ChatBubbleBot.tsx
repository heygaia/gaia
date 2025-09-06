// ChatBubbleBot.tsx
import { useCallback, useMemo, useRef } from "react";

import { SystemPurpose } from "@/features/chat/api/chatApi";
import ChatBubble_Actions from "@/features/chat/components/bubbles/actions/ChatBubble_Actions";
import ChatBubble_Actions_Image from "@/features/chat/components/bubbles/actions/ChatBubble_Actions_Image";
import { IntegrationConnectionPrompt } from "@/features/chat/components/integration/IntegrationConnectionPrompt";
import MemoryIndicator from "@/features/chat/components/memory/MemoryIndicator";
import { useLoading } from "@/features/chat/hooks/useLoading";
import { ChatBubbleBotProps } from "@/types/features/chatBubbleTypes";
import { ImageData, MemoryData } from "@/types/features/toolDataTypes";
import { parseDate } from "@/utils/date/dateUtils";
import { renderToolData } from "@/utils/toolDataNormalizer";

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
    integration_connection_required,
  } = props;
  const { isLoading } = useLoading();

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
    // Integration connection prompt takes priority
    if (integration_connection_required)
      return (
        <IntegrationConnectionPrompt data={integration_connection_required} />
      );

    if (image_data)
      return renderToolData(
        image_data,
        (imageItem: ImageData, index: number) => (
          <ImageBubble key={index} {...props} image_data={imageItem} />
        ),
      );

    return <TextBubble {...props} />;
  }, [image_data, props]);

  return (
    (loading ||
      image_data ||
      !!text ||
      props.integration_connection_required ||
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
              <>
                {renderToolData(
                  memory_data,
                  (memoryItem: MemoryData, index: number) => (
                    <div key={index}>
                      <MemoryIndicator
                        memoryData={memoryItem}
                        onOpenModal={onOpenMemoryModal}
                      />
                    </div>
                  ),
                )}
              </>
            )}
            <div className="chat_bubble_container">{renderedComponent}</div>
          </div>
        </div>

        {!loading && !isLoading && (
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
              <>
                {renderToolData(
                  image_data,
                  (imageItem: ImageData, index: number) => (
                    <div key={index}>
                      <ChatBubble_Actions_Image
                        key={index}
                        image_data={imageItem}
                      />
                    </div>
                  ),
                )}
              </>
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
