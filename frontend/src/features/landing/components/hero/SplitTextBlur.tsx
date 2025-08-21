import { motion } from "framer-motion";
import React, { useRef } from "react";

import { useIntersectionObserver } from "@/hooks/ui/useIntersectionObserver";
import { cn } from "@/lib/utils";

interface SplitTextBlurProps {
  text: string;
  className?: string;
  delay?: number;
  staggerDelay?: number;
  springConfig?: {
    stiffness: number;
    damping: number;
    mass: number;
  };
  yOffset?: number;
}

const SplitTextBlur = ({
  text,
  className = "",
  delay = 1,
  staggerDelay = 0.1,
  springConfig = {
    stiffness: 400,
    damping: 70,
    mass: 1,
  },
  yOffset = 2,
}: SplitTextBlurProps) => {
  const ref = useRef<HTMLDivElement>(null);
  const isVisible = useIntersectionObserver(ref, { threshold: 0.1 });

  const words = text.split(" ");

  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        delay: delay,
        when: "beforeChildren",
        staggerChildren: staggerDelay,
      },
    },
  };

  const wordVariants = {
    hidden: {
      opacity: 0,
      filter: "blur(10px)",
      y: yOffset,
    },
    visible: {
      opacity: 1,
      filter: "blur(0px)",
      y: 0,
      transition: {
        type: "spring" as const,
        stiffness: springConfig.stiffness,
        damping: springConfig.damping,
        mass: springConfig.mass,
      },
    },
  };

  return (
    <motion.div
      ref={ref}
      initial="hidden"
      animate={isVisible ? "visible" : "hidden"}
      variants={containerVariants}
      className={cn(className)}
      style={{ willChange: "transform, opacity, filter" }}
    >
      {words.map((word, index) => (
        <motion.span
          key={index}
          variants={wordVariants}
          style={{
            willChange: "transform, opacity, filter",
            display: "inline-block",
            marginRight: index < words.length - 1 ? "0.25em" : "0",
          }}
        >
          {word}
        </motion.span>
      ))}
    </motion.div>
  );
};

// Usage example with your div
const HeroText = () => {
  return (
    <SplitTextBlur
      text="Meet the AI assistant that actually works"
      className="max-w-(--breakpoint-md) py-3 text-center font-inter text-[5.13rem] font-medium text-white sm:text-7xl"
      delay={1}
      staggerDelay={0.1}
      springConfig={{
        stiffness: 400,
        damping: 70,
        mass: 1,
      }}
      yOffset={2}
    />
  );
};

export { HeroText, SplitTextBlur };
