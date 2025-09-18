// src/features/mail/components/MailAnimationWrapper.tsx

import { AnimatePresence, motion } from "framer-motion";
import { Bot, User } from "lucide-react";
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
    }, 800); // Slightly increased delay for better pacing

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
              scale: { duration: 0.4 },
            }}
            className="flex w-full items-start justify-end gap-3"
          >
            <div className="max-w-md rounded-2xl rounded-tr-md border border-white/10 bg-gradient-to-br from-slate-700/90 to-slate-800/90 px-5 py-3 text-sm break-words whitespace-pre-wrap text-white shadow-lg shadow-black/20 backdrop-blur-sm">
              {step.prompt}
            </div>
            <div className="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-full border border-white/10 bg-gradient-to-br from-slate-600 to-slate-700 shadow-lg shadow-black/20">
              <User className="h-5 w-5 text-white" />
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
              duration: 0.7,
              ease: [0.22, 1, 0.36, 1],
              scale: { duration: 0.5 },
            }}
            className="flex w-full items-start justify-start gap-3"
          >
            <div className="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-full border border-[#01BBFF]/20 bg-gradient-to-br from-[#01BBFF] to-cyan-400 shadow-lg shadow-[#01BBFF]/20">
              <Bot className="h-5 w-5 text-white" />
            </div>
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

  // Automatically cycle through the animation steps every 8 seconds
  useEffect(() => {
    const stepInterval = setInterval(() => {
      setActiveStep((prev) => (prev + 1) % animationSteps.length);
    }, 8000);
    return () => clearInterval(stepInterval);
  }, []);

  return (
    <div className="mx-auto w-full max-w-4xl">
      {/* Navigation Pills */}
      <div className="mb-8 flex justify-center space-x-2">
        {animationSteps.map((step, index) => (
          <button
            key={step.name}
            onClick={() => setActiveStep(index)}
            className="group relative rounded-full px-5 py-2.5 text-sm font-medium text-gray-300 transition-all duration-300 hover:text-white focus:outline-none"
          >
            {activeStep === index && (
              <motion.div
                layoutId="active-mail-pill"
                className="absolute inset-0 rounded-full border border-white/10 bg-gradient-to-br from-white/10 to-white/5 shadow-lg backdrop-blur-sm"
                transition={{ type: "spring", stiffness: 400, damping: 35 }}
              />
            )}
            <span className="relative z-10 flex items-center gap-2">
              {React.cloneElement(step.icon, {
                className: `h-4 w-4 transition-colors duration-300 ${
                  activeStep === index
                    ? "text-[#01BBFF]"
                    : "text-gray-400 group-hover:text-white"
                }`,
              })}
              <span
                className={`transition-colors duration-300 ${
                  activeStep === index
                    ? "font-semibold text-[#01BBFF]"
                    : "text-gray-300 group-hover:text-white"
                }`}
              >
                {step.name}
              </span>
            </span>
          </button>
        ))}
      </div>

      {/* Main Animation Area */}
      <div className="relative flex min-h-[650px] items-start rounded-2xl border border-white/10 p-6">
        {/* <div className="absolute inset-0 bg-gradient-to-r from-[#01BBFF]/5 via-transparent to-cyan-400/5 rounded-2xl" /> */}
        <div className="relative z-10 w-full">
          {/* Using key={activeStep} on AnimatedChat ensures it re-mounts and runs its
              internal animation sequence from the beginning every time the step changes. */}
          <AnimatedChat key={activeStep} step={animationSteps[activeStep]} />
        </div>
      </div>
    </div>
  );
}
