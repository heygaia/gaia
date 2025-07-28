import { motion } from "framer-motion";
import Image from "next/image";

import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui";
import { useUser } from "@/features/auth/hooks/useUser";
import {
  SimpleChatBubbleBot,
  SimpleChatBubbleUser,
} from "@/features/landing/components/demo/SimpleChatBubbles";

import { Message } from "../types";

interface OnboardingMessagesProps {
  messages: Message[];
  messagesEndRef: React.RefObject<HTMLDivElement | null>;
}

export const OnboardingMessages = ({
  messages,
  messagesEndRef,
}: OnboardingMessagesProps) => {
  const user = useUser();

  return (
    <>
      {messages.map((message, index) => {
        // Streamlined consecutive message detection
        const prevMessage = messages[index - 1];
        const nextMessage = messages[index + 1];
        const isConsecutivePrev = prevMessage?.type === message.type;
        const isConsecutiveNext = nextMessage?.type === message.type;

        // Simplified delay calculation
        const totalDelay = index * 0.05 + (isConsecutivePrev ? 0.4 : 0);

        return (
          <motion.div
            key={message.id}
            className="mb-3"
            initial={{ opacity: 0, y: 15 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{
              duration: 0.4,
              ease: "easeOut",
              delay: totalDelay,
            }}
          >
            {message.type === "bot" ? (
              <div className="relative flex items-center gap-2">
                {!isConsecutiveNext && (
                  <Image
                    alt="GAIA Logo"
                    src={"/branding/logo.webp"}
                    width={30}
                    height={30}
                    className="absolute bottom-0 -left-10 mt-3 size-[30px]"
                  />
                )}
                <SimpleChatBubbleBot>{message.content}</SimpleChatBubbleBot>
              </div>
            ) : (
              <div className="relative flex w-full items-center justify-end gap-2">
                <SimpleChatBubbleUser>{message.content}</SimpleChatBubbleUser>

                <div className="absolute -right-12 mt-3 min-w-[40px]">
                  <Avatar className="rounded-full bg-black">
                    <AvatarImage src={user?.profilePicture} alt="User Avatar" />
                    <AvatarFallback>
                      <Image
                        src={"/media/default.webp"}
                        width={35}
                        height={35}
                        alt="Default profile picture"
                      />
                    </AvatarFallback>
                  </Avatar>
                </div>
              </div>
            )}
          </motion.div>
        );
      })}
      <div ref={messagesEndRef} />
    </>
  );
};
