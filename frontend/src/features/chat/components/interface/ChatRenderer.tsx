import { Spinner } from "@heroui/spinner";
import Image from "next/image";
import { useParams, useSearchParams } from "next/navigation";
import { useEffect, useMemo, useRef, useState } from "react";

import ChatBubbleBot from "@/features/chat/components/bubbles/bot/ChatBubbleBot";
import SearchedImageDialog from "@/features/chat/components/bubbles/bot/SearchedImageDialog";
import ChatBubbleUser from "@/features/chat/components/bubbles/user/ChatBubbleUser";
import GeneratedImageSheet from "@/features/chat/components/image/GeneratedImageSheet";
import StarterText from "@/features/chat/components/interface/StarterText";
import MemoryModal from "@/features/chat/components/memory/MemoryModal";
import { useConversation } from "@/features/chat/hooks/useConversation";
import { useConversationList } from "@/features/chat/hooks/useConversationList";
import { useLoading } from "@/features/chat/hooks/useLoading";
import { useLoadingText } from "@/features/chat/hooks/useLoadingText";
import { filterEmptyMessagePairs } from "@/features/chat/utils/messageContentUtils";
import { getMessageProps } from "@/features/chat/utils/messagePropsUtils";
import { getToolCategoryIcon } from "@/features/chat/utils/toolIcons";
import { SetImageDataType } from "@/types/features/chatBubbleTypes";
import { MessageType } from "@/types/features/convoTypes";

export default function ChatRenderer() {
  const { convoMessages } = useConversation();
  const { conversations } = useConversationList();
  const [openGeneratedImage, setOpenGeneratedImage] = useState<boolean>(false);
  const [openMemoryModal, setOpenMemoryModal] = useState<boolean>(false);
  const searchParams = useSearchParams();
  const messageId = searchParams.get("messageId");
  const { isLoading } = useLoading();
  const { loadingText, toolInfo } = useLoadingText();
  const { id: convoIdParam } = useParams<{ id: string }>();
  const scrolledToMessageRef = useRef<string | null>(null);
  const [imageData, setImageData] = useState<SetImageDataType>({
    src: "",
    prompt: "",
    improvedPrompt: "",
  });

  const conversation = useMemo(() => {
    return conversations.find(
      (convo) => convo.conversation_id === convoIdParam,
    );
  }, [conversations, convoIdParam]);

  // Create options object for getMessageProps
  const messagePropsOptions = {
    conversation,
    setImageData,
    setOpenGeneratedImage,
    setOpenMemoryModal,
  };

  // Filter out empty message pairs
  const filteredMessages = useMemo(() => {
    if (!convoMessages) return [];

    return filterEmptyMessagePairs(
      convoMessages,
      conversation?.is_system_generated || false,
      conversation?.system_purpose,
    );
  }, [
    convoMessages,
    conversation?.is_system_generated,
    conversation?.system_purpose,
  ]);

  useEffect(() => {
    if (
      messageId &&
      filteredMessages.length > 0 &&
      scrolledToMessageRef.current !== messageId
    ) {
      scrollToMessage(messageId);
      scrolledToMessageRef.current = messageId;
    }
  }, [messageId, filteredMessages]);

  const scrollToMessage = (messageId: string) => {
    if (!messageId) return;

    const messageElement = document.getElementById(messageId);

    if (!messageElement) return;

    messageElement.scrollIntoView({ behavior: "smooth", block: "start" });
    messageElement.style.transition = "all 0.3s ease";

    setTimeout(() => {
      messageElement.style.scale = "1.07";

      setTimeout(() => {
        messageElement.style.scale = "1";
      }, 300);
    }, 700);
  };

  if (!!filteredMessages && filteredMessages?.length === 0) {
    return (
      <div className="relative flex flex-1 flex-col items-center justify-center gap-2">
        <Image
          alt="GAIA Logo"
          src={"/branding/logo.webp"}
          width={110}
          height={110}
        />
        <StarterText />
      </div>
    );
  }

  return (
    <>
      <title id="chat_title">
        {`${
          conversations.find((convo) => convo.conversation_id === convoIdParam)
            ?.description || "New chat"
        } | GAIA`}
      </title>

      <GeneratedImageSheet
        imageData={imageData}
        openImage={openGeneratedImage}
        setOpenImage={setOpenGeneratedImage}
      />

      <MemoryModal
        isOpen={openMemoryModal}
        onClose={() => setOpenMemoryModal(false)}
      />

      <SearchedImageDialog />

      {filteredMessages?.map((message: MessageType, index: number) =>
        message.type === "bot" ? (
          <div
            key={message.message_id || index}
            className="relative flex items-end gap-1 pt-1 pb-5 pl-1"
          >
            <div className="min-w-[40px]">
              <Image
                alt="GAIA Logo"
                src={"/branding/logo.webp"}
                width={30}
                height={30}
                className={`${isLoading ? "opacity-0" : "opacity-100"} relative transition duration-150`}
              />
            </div>

            <ChatBubbleBot
              {...getMessageProps(message, "bot", messagePropsOptions)}
            />
          </div>
        ) : (
          <ChatBubbleUser
            key={message.message_id || index}
            {...getMessageProps(message, "user", messagePropsOptions)}
          />
        ),
      )}
      {isLoading && (
        <div className="flex items-center gap-4 pt-3 pl-[40px] text-sm font-medium">
          {toolInfo?.toolCategory && (
            <>
              {getToolCategoryIcon(toolInfo.toolCategory, {
                size: 18,
                width: 18,
                height: 18,
              })}
            </>
          )}
          <span>{loadingText || "GAIA is thinking..."}</span>
          <Spinner variant="dots" color="primary" />
        </div>
      )}
    </>
  );
}
