import { Info } from "lucide-react";
import Image from "next/image";

import {
  Brain02Icon,
  CheckmarkCircle02Icon,
  FileEmpty02Icon,
  Image02Icon,
  SourceCodeCircleIcon,
  Target02Icon,
} from "@/components/shared/icons";

interface IconProps {
  size?: number;
  width?: number;
  height?: number;
  strokeWidth?: number;
  className?: string;
}

export const getToolCategoryIcon = (
  category: string,
  iconProps: IconProps = {},
) => {
  const defaultProps = {
    size: iconProps.size || 16,
    width: iconProps.width || 20,
    height: iconProps.height || 20,
    strokeWidth: iconProps.strokeWidth || 2,
    className: iconProps.className,
  };

  switch (category) {
    // Registry categories from backend
    case "mail":
      return (
        <Image
          alt={`${category} Icon`}
          {...defaultProps}
          className={`${iconProps.className} aspect-square object-contain`}
          src="/images/icons/gmail.svg"
        />
      );
    case "calendar":
      return (
        <Image
          alt={`${category} Icon`}
          {...defaultProps}
          className={`${iconProps.className} aspect-square object-contain`}
          src="/images/icons/googlecalendar.webp"
        />
      );
    case "productivity":
      return (
        <CheckmarkCircle02Icon
          {...defaultProps}
          className={iconProps.className || "text-emerald-400"}
        />
      );

    case "documents":
      return (
        <FileEmpty02Icon
          {...defaultProps}
          className={iconProps.className || "text-orange-400"}
        />
      );
    case "google_docs":
      return (
        <Image
          alt={`${category} Icon`}
          {...defaultProps}
          className={`${iconProps.className} aspect-square object-contain`}
          src="/images/icons/google_docs.webp"
        />
      );
    case "development":
      return (
        <SourceCodeCircleIcon
          {...defaultProps}
          className={iconProps.className || "text-cyan-400"}
        />
      );
    case "search":
      return (
        <Image
          alt={`${category} Icon`}
          {...defaultProps}
          className={`${iconProps.className} aspect-square object-contain`}
          src="https://upload.wikimedia.org/wikipedia/commons/c/c1/Google_%22G%22_logo.svg"
        />
      );
    case "memory":
      return (
        <Brain02Icon
          {...defaultProps}
          className={iconProps.className || "text-indigo-400"}
        />
      );
    case "creative":
      return (
        <Image02Icon
          {...defaultProps}
          className={iconProps.className || "text-pink-400"}
        />
      );
    case "weather":
      return (
        <Image
          alt={`${category} Icon`}
          {...defaultProps}
          className={`${iconProps.className} aspect-square object-contain`}
          src="https://upload.wikimedia.org/wikipedia/commons/1/1e/Weather_%28iOS%29.png"
        />
      );
    case "goal_tracking":
      return (
        <Target02Icon
          {...defaultProps}
          className={iconProps.className || "text-emerald-400"}
        />
      );
    case "notion":
      return (
        <Image
          alt={`${category} Icon`}
          {...defaultProps}
          className={`${iconProps.className} aspect-square object-contain`}
          src="/images/icons/notion.webp"
        />
      );
    case "webpage":
      return (
        <Info
          {...defaultProps}
          className={iconProps.className || "text-purple-400"}
        />
      );
    case "support":
      return (
        <Info
          {...defaultProps}
          className={iconProps.className || "text-blue-400"}
        />
      );
    case "general":
      return (
        <Info
          {...defaultProps}
          className={iconProps.className || "text-gray-400"}
        />
      );
    default:
      return null;
  }
};
