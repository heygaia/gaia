"use client";

import { motion } from "framer-motion";
import { useState } from "react";

import {
  Cancel01Icon,
  Gmail,
  GoogleCalendarIcon,
  GoogleDrive,
  Notion,
} from "@/components/shared/icons";
import { SelectedWorkflowData } from "@/features/chat/hooks/useWorkflowSelection";

interface SelectedWorkflowIndicatorProps {
  workflow: SelectedWorkflowData | null;
  onRemove?: () => void;
}

export default function SelectedWorkflowIndicator({
  workflow,
  onRemove,
}: SelectedWorkflowIndicatorProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  // Return null if no workflow is selected
  if (!workflow) {
    return null;
  }

  const allLogos = [
    <Gmail key="gmail" className={isExpanded ? "h-6 w-6" : "h-5 w-5"} />,
    <GoogleCalendarIcon
      key="calendar"
      className={isExpanded ? "h-6 w-6" : "h-5 w-5"}
    />,
    <GoogleDrive key="drive" className={isExpanded ? "h-6 w-6" : "h-5 w-5"} />,
    <Notion key="notion" className={isExpanded ? "h-6 w-6" : "h-5 w-5"} />,
  ];

  const visibleLogos = allLogos.slice(0, 2);
  const remainingCount = allLogos.length - 2;

  return (
    <div className={`${isExpanded ? "p-3" : "p-3"} select-none`}>
      <motion.div
        className="relative w-fit cursor-pointer overflow-hidden bg-zinc-700 p-4 text-white"
        layout
        initial={{ width: 300 }}
        animate={{
          width: isExpanded ? 270 : 320,
          borderRadius: isExpanded ? "var(--radius-2xl)" : "var(--radius-xl)",
          height: isExpanded ? 220 : 40,
        }}
        transition={{
          type: "spring",
          stiffness: 300,
          damping: 20,
          mass: 0.8,
        }}
        onClick={() => setIsExpanded(!isExpanded)}
        whileHover={{ scale: isExpanded ? 1.02 : 1.03 }}
        whileTap={{ scale: isExpanded ? 1.06 : 0.98 }}
      >
        {isExpanded ? (
          // Expanded state - vertical layout with close icon in the icons row
          <div className="flex h-full flex-col">
            <div className="mb-4 flex items-center justify-between">
              <div className="flex items-center space-x-2">{allLogos}</div>
              {onRemove && (
                <motion.button
                  initial={{ scale: 0 }}
                  animate={{ scale: 1 }}
                  transition={{ duration: 0.2 }}
                  className="mr-1 cursor-pointer rounded-md bg-zinc-600 p-1 text-zinc-300 transition hover:bg-zinc-800 hover:text-white"
                  onClick={(e) => {
                    e.stopPropagation();
                    onRemove();
                  }}
                >
                  <Cancel01Icon className="h-5 w-5" />
                </motion.button>
              )}
            </div>

            <div className="mb-2">
              <h3 className="text-base font-normal">{workflow.title}</h3>
            </div>

            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{
                type: "spring",
                stiffness: 400,
                damping: 25,
                delay: 0.1,
              }}
              className="flex-1 space-y-3"
            >
              <p className="text-sm leading-relaxed font-light text-zinc-200">
                {workflow.description}
              </p>
              <p className="text-xs text-zinc-400">
                {workflow.steps.length} step
                {workflow.steps.length !== 1 ? "s" : ""}
              </p>
            </motion.div>
          </div>
        ) : (
          // Collapsed state - horizontal layout
          <div className="flex h-full w-full items-center justify-between gap-3">
            <div className="flex min-w-0 flex-1 items-center gap-3">
              <div className="flex flex-shrink-0 items-center space-x-1">
                {visibleLogos}
                <div className="flex h-7 w-7 items-center justify-center rounded-md bg-zinc-600 text-xs font-medium">
                  +{remainingCount}
                </div>
              </div>
              <h3 className="min-w-0 truncate text-sm font-normal">
                {workflow.title}
              </h3>
            </div>
            <motion.div
              animate={{ rotate: isExpanded ? 180 : 0 }}
              transition={{ duration: 0.2 }}
              className="flex-shrink-0 text-zinc-300"
            >
              <svg
                className="h-5 w-5"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
              >
                <path d="m18 15-6-6-6 6" />
              </svg>
            </motion.div>
          </div>
        )}
      </motion.div>
    </div>
  );
}
