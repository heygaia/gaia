// src/features/mail/components/MailAnimationWrapper.tsx

import { AnimatePresence, motion } from "framer-motion";
import { Chip } from "@heroui/chip";
import React, { useEffect, useState } from "react";

import { animationSteps } from "./mail-animation.data";

/**
 * Renders a single "turn" in the conversation, including the user's prompt
 * and the bot's animated response, all in the correct sequence.
 */
const AnimatedChat = ({ step }: { step: (typeof animationSteps)[0] }) => {
  // State to manage the animation sequence within a single chat turn
  const [showUserPrompt, setShowUserPrompt] = useState(false);
  const [showBotResponse, setShowBotResponse] = useState(false);

  useEffect(() => {
    // This effect runs once when the component mounts, orchestrating the animation.
    // 1. Show user prompt immediately.
    setShowUserPrompt(true);

    // 2. After a delay, show the bot's final response.
    const responseTimer = setTimeout(() => {
      setShowBotResponse(true);
    }, 400); // Reduced delay for quicker animation

    // Cleanup timers on component unmount
    return () => {
      clearTimeout(responseTimer);
    };
  }, []); // Empty dependency array ensures this runs only once on mount

  return (
    <div className="w-full space-y-6">
      {/* User Prompt */}
      <AnimatePresence>
        {showUserPrompt && (
          <motion.div
            key="user-prompt"
            initial={{ opacity: 0, y: 20, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            transition={{
              type: "spring",
              damping: 25,
              stiffness: 120,
              duration: 0.3,
            }}
            className="flex w-full items-start justify-end"
          >
            <div className="max-w-md rounded-3xl rounded-br-none border border-[#00bbff]/20 bg-[#00bbff] px-4 py-3 text-base break-words whitespace-pre-wrap text-black">
              {step.prompt}
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Bot Response */}
      <AnimatePresence>
        {showBotResponse && (
          <motion.div
            key="bot-response"
            initial={{ opacity: 0, y: 20, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            transition={{
              duration: 0.4,
              ease: [0.22, 1, 0.36, 1],
            }}
            className="flex w-full items-start justify-start"
          >
            <div className="max-w-2xl min-w-0 flex-1">{step.component}</div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

/**
 * Main wrapper component that controls the overall animation flow.
 */
export default function MailAnimationWrapper() {
  const [activeStep, setActiveStep] = useState(0);

  // Automatically cycle through the animation steps every 5 seconds (reduced from 8)
  useEffect(() => {
    const stepInterval = setInterval(() => {
      setActiveStep((prev) => (prev + 1) % animationSteps.length);
    }, 5000);
    return () => clearInterval(stepInterval);
  }, []);

  return (
    <div className="mx-auto w-full max-w-4xl">
      {/* Navigation Pills */}
      <div className="mb-8 flex justify-center space-x-2">
        {animationSteps.map((step, index) => (
          <Chip
            key={step.name}
            color={activeStep === index ? "primary" : "default"}
            radius="sm"
            size="lg"
            className={"flex cursor-pointer gap-1 pl-3"}
            onClick={() => setActiveStep(index)}
            startContent={React.cloneElement(step.icon, {
              color: undefined,
              className: `h-4 w-4`,
            })}
          >
            {step.name}
          </Chip>
        ))}
      </div>

      {/* Main Animation Area */}
      <div className="relative flex min-h-[650px] items-start p-6">
        <div className="relative z-10 w-full">
          {/* Using key={activeStep} on AnimatedChat ensures it re-mounts and runs its
              internal animation sequence from the beginning every time the step changes. */}
          <AnimatedChat key={activeStep} step={animationSteps[activeStep]} />
        </div>
      </div>
    </div>
  );
}
