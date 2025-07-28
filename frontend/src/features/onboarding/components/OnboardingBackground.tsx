"use client";

import { motion } from "framer-motion";

export function OnboardingBackground({
  opacity = [0.8, 1, 0.8],
  speed = 4,
}: {
  opacity?: number[];
  speed?: number;
}) {
  return (
    <motion.div
      className="absolute inset-0 z-0"
      style={{
        backgroundImage: `radial-gradient(100% 125% at 50% 100%, #000000 50%, #00bbffAA)`,
      }}
      animate={{
        opacity,
      }}
      transition={{
        duration: speed,
        repeat: Infinity,
        ease: "easeInOut",
      }}
    />
  );
}
