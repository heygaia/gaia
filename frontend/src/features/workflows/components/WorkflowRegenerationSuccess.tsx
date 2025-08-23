import { motion } from "framer-motion";
import { CheckCircle, Sparkles } from "lucide-react";

interface WorkflowRegenerationSuccessProps {
  stepsCount: number;
  onComplete?: () => void;
}

export default function WorkflowRegenerationSuccess({
  stepsCount,
  onComplete,
}: WorkflowRegenerationSuccessProps) {
  return (
    <motion.div
      className="space-y-4"
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.5 }}
      onAnimationComplete={() => {
        // Auto complete after animation
        setTimeout(() => {
          onComplete?.();
        }, 2000);
      }}
    >
      <div className="flex flex-col items-center justify-center py-4">
        <div className="text-center">
          {/* Success Icon with Animation */}
          <motion.div
            className="mb-4"
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            transition={{ delay: 0.2, type: "spring", stiffness: 200 }}
          >
            <div className="relative">
              <CheckCircle className="h-12 w-12 text-success" />
              {/* Sparkle effects */}
              <motion.div
                className="absolute -top-2 -right-2"
                animate={{
                  rotate: [0, 180, 360],
                  scale: [1, 1.2, 1],
                }}
                transition={{ duration: 2, repeat: Infinity }}
              >
                <Sparkles className="h-4 w-4 text-yellow-400" />
              </motion.div>
              <motion.div
                className="absolute -bottom-1 -left-1"
                animate={{
                  rotate: [360, 180, 0],
                  scale: [1, 1.1, 1],
                }}
                transition={{ duration: 1.8, repeat: Infinity, delay: 0.5 }}
              >
                <Sparkles className="h-3 w-3 text-blue-400" />
              </motion.div>
            </div>
          </motion.div>

          {/* Success Text */}
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4 }}
          >
            <h3 className="text-lg font-medium text-success">
              Steps Regenerated!
            </h3>
            <p className="text-sm text-zinc-400">
              {stepsCount} new steps generated successfully
            </p>
          </motion.div>

          {/* Celebration particles effect */}
          <motion.div
            className="relative mt-4"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.6 }}
          >
            {[...Array(6)].map((_, i) => (
              <motion.div
                key={i}
                className="absolute h-1 w-1 rounded-full bg-gradient-to-r from-blue-400 to-purple-400"
                style={{
                  left: `${20 + (i % 3) * 20}%`,
                  top: `${(i % 2) * 10}px`,
                }}
                animate={{
                  y: [-10, -30, -10],
                  opacity: [1, 0.5, 1],
                  scale: [1, 1.5, 1],
                }}
                transition={{
                  duration: 2,
                  repeat: Infinity,
                  delay: i * 0.2,
                }}
              />
            ))}
          </motion.div>
        </div>
      </div>
    </motion.div>
  );
}
