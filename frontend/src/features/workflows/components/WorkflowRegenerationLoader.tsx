import { Spinner } from "@heroui/spinner";
import { motion } from "framer-motion";
import { RefreshCw, Sparkles } from "lucide-react";

interface WorkflowRegenerationLoaderProps {
  reason?: string;
  workflowTitle?: string;
}

export default function WorkflowRegenerationLoader({
  reason,
  workflowTitle,
}: WorkflowRegenerationLoaderProps) {
  return (
    <div className="space-y-6">
      <div className="flex flex-col items-center justify-center py-8">
        <div className="text-center">
          {/* Animated Icon */}
          <motion.div
            className="mb-6"
            animate={{ rotate: 360 }}
            transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
          >
            <div className="relative">
              <RefreshCw className="h-12 w-12 text-blue-400" />
              <motion.div
                className="absolute -top-1 -right-1"
                animate={{ scale: [1, 1.2, 1] }}
                transition={{ duration: 1.5, repeat: Infinity }}
              >
                <Sparkles className="h-4 w-4 text-yellow-400" />
              </motion.div>
            </div>
          </motion.div>

          {/* Loading Text */}
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
          >
            <h3 className="text-lg font-medium text-zinc-100">
              Regenerating Workflow Steps
            </h3>
            <p className="mt-2 text-sm text-zinc-400">
              {reason && workflowTitle
                ? `${reason} for: "${workflowTitle}"`
                : "AI is creating new workflow steps..."}
            </p>
          </motion.div>

          {/* Animated Progress Dots */}
          <motion.div
            className="mt-6 flex items-center justify-center space-x-1"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.4 }}
          >
            {[0, 1, 2].map((i) => (
              <motion.div
                key={i}
                className="h-2 w-2 rounded-full bg-blue-400"
                animate={{
                  scale: [1, 1.2, 1],
                  opacity: [0.3, 1, 0.3],
                }}
                transition={{
                  duration: 1.5,
                  repeat: Infinity,
                  delay: i * 0.2,
                }}
              />
            ))}
          </motion.div>

          {/* Additional Status Text */}
          <motion.div
            className="mt-4 animate-pulse text-xs text-zinc-500"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.6 }}
          >
            ✨ This may take a few moments...
          </motion.div>
        </div>
      </div>
    </div>
  );
}
