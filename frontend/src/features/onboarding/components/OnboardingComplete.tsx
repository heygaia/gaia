import { Button } from "@heroui/button";
import { motion } from "framer-motion";
import { ArrowRight } from "lucide-react";

interface OnboardingCompleteProps {
  onLetsGo: () => void;
}

export const OnboardingComplete = ({ onLetsGo }: OnboardingCompleteProps) => {
  return (
    <motion.div
      className="mx-auto mb-7 w-full max-w-2xl text-center"
      initial={{ opacity: 0, scale: 0.9, y: 15 }}
      animate={{ opacity: 1, scale: 1, y: 0 }}
      transition={{
        duration: 0.5,
        ease: "easeOut",
        delay: 0.2,
      }}
    >
      <Button
        onPress={onLetsGo}
        color="primary"
        endContent={<ArrowRight width={17} height={17} />}
        className="transition-all! hover:-translate-y-1 hover:scale-110 hover:bg-primary/90"
      >
        <span className="flex items-center gap-2">Let's Go!</span>
      </Button>
    </motion.div>
  );
};
