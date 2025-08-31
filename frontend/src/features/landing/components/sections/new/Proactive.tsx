import "reactflow/dist/style.css";

import { AnimatePresence, motion } from "framer-motion";
import {
  Archive,
  ArrowRight,
  Calendar,
  Check,
  CheckCircle,
  ChevronDown,
  Clock,
  FileText,
  Image as ImageIcon,
  Mail,
  MousePointer2,
  Reply,
  Star,
  Target,
  Type,
  Zap,
} from "lucide-react";
import React, {
  ElementType,
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import { useInView } from "react-intersection-observer";
// 👇 React Flow imports are correct. Added Handle for the custom node.
import ReactFlow, {
  Edge,
  Handle,
  MarkerType,
  Node,
  NodeProps,
  Position,
  useEdgesState,
  useNodesState,
} from "reactflow";

import SectionChip from "../../shared/SectionChip";
// Note: These imports point to dummy files in your original code.
// Ensure your project has a 'demo-data.ts' file that exports these types and values.
import { DemoData } from "./demo-data";
import { demoContents } from "./demo-data";

const wait = (ms: number): Promise<void> =>
  new Promise((resolve) => setTimeout(resolve, ms));

const LargeHeader: React.FC<{
  headingText: string;
  subHeadingText: string;
}> = ({ headingText, subHeadingText }) => (
  <header className="text-center">
    <SectionChip icon={Zap} text="Proactive Intelligence" />

    <motion.h1
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.7, ease: [0.25, 0.46, 0.45, 0.94], delay: 0.1 }}
      className="mb-6 bg-gradient-to-r from-white to-gray-400 bg-clip-text text-3xl leading-tight font-bold text-transparent md:text-4xl lg:text-5xl xl:text-6xl"
    >
      {headingText}
    </motion.h1>
    <motion.p
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.7, ease: [0.25, 0.46, 0.45, 0.94], delay: 0.2 }}
      className="mx-auto max-w-4xl text-base leading-relaxed text-gray-400 md:text-lg lg:text-xl"
    >
      {subHeadingText}
    </motion.p>
  </header>
);

const GoogleLogo: React.FC<{
  src: string;
  alt: string;
  className?: string;
}> = ({ src, alt, className }) => (
  <motion.img
    src={src}
    alt={alt}
    className={`object-contain ${className}`}
    initial={{ opacity: 0, scale: 0.8 }}
    animate={{ opacity: 1, scale: 1 }}
    exit={{ opacity: 0, scale: 0.8 }}
    transition={{ duration: 0.4, ease: [0.25, 0.46, 0.45, 0.94] }}
  />
);

const GmailView: React.FC<{
  isExpanded: boolean;
  highlightTrigger: boolean;
  content: DemoData["email"];
}> = ({ isExpanded, highlightTrigger, content }) => {
  const containerVariants = {
    collapsed: { height: "80px" },
    expanded: { height: "400px" },
  };

  return (
    <motion.div
      layoutId="main-container"
      variants={containerVariants}
      initial="collapsed"
      animate={isExpanded ? "expanded" : "collapsed"}
      transition={{ duration: 0.8, ease: [0.25, 0.46, 0.45, 0.94] }}
      className="w-full max-w-3xl overflow-hidden rounded-2xl bg-[#F2F6FC] shadow-2xl"
    >
      <div className="flex h-full flex-col p-4">
        <motion.div
          layout="position"
          className="flex flex-shrink-0 items-center gap-4"
        >
          <GoogleLogo
            src="https://upload.wikimedia.org/wikipedia/commons/7/7e/Gmail_icon_%282020%29.svg"
            alt="Gmail"
            className="h-8 w-8"
          />
          <div className="min-w-0 flex-1">
            <h3 className="truncate text-base font-semibold text-gray-800">
              {content.subject}
            </h3>
            <p className="truncate text-sm text-gray-600">
              {content.sender} &lt;{content.senderEmail}&gt;
            </p>
          </div>
          <div className="flex flex-shrink-0 items-center gap-4 text-gray-500">
            <Star className="h-5 w-5 transition-colors duration-200 hover:text-yellow-500" />
            <Archive className="h-5 w-5 transition-colors duration-200 hover:text-gray-800" />
            <Reply className="h-5 w-5 transition-colors duration-200 hover:text-gray-800" />
          </div>
        </motion.div>

        <AnimatePresence>
          {isExpanded && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{
                opacity: 1,
                y: 0,
                transition: {
                  delay: 0.3,
                  duration: 0.6,
                  ease: [0.25, 0.46, 0.45, 0.94],
                },
              }}
              exit={{ opacity: 0 }}
              className="mt-4 flex-grow space-y-4 overflow-auto border-t border-gray-200 pt-4"
            >
              <p className="text-sm leading-relaxed text-gray-700">
                {content.body(highlightTrigger)}
              </p>
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{
                  opacity: 1,
                  y: 0,
                  transition: {
                    delay: 1.2,
                    duration: 0.6,
                    ease: [0.25, 0.46, 0.45, 0.94],
                  },
                }}
                className="flex items-center gap-3 rounded-xl border border-[#01BBFF]/20 bg-[#01BBFF]/5 p-4 text-sm text-[#01BBFF]"
              >
                <Zap className="h-5 w-5 flex-shrink-0 text-[#01BBFF]" />
                <span className="font-medium">
                  GAIA is creating your action plan...
                </span>
                <div className="ml-auto flex space-x-1">
                  <div
                    className="h-1.5 w-1.5 animate-bounce rounded-full bg-[#01BBFF]"
                    style={{ animationDelay: "0s" }}
                  ></div>
                  <div
                    className="h-1.5 w-1.5 animate-bounce rounded-full bg-[#01BBFF]"
                    style={{ animationDelay: "0.1s" }}
                  ></div>
                  <div
                    className="h-1.5 w-1.5 animate-bounce rounded-full bg-[#01BBFF]"
                    style={{ animationDelay: "0.2s" }}
                  ></div>
                </div>
              </motion.div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </motion.div>
  );
};

const CalendarView: React.FC<{
  content: DemoData["calendar"];
  emailContent: DemoData["email"];
}> = ({ content, emailContent }) => (
  <motion.div
    layoutId="main-container"
    className="flex h-[500px] w-full max-w-5xl flex-col overflow-hidden rounded-2xl bg-white shadow-2xl md:h-[450px] md:flex-row"
    initial={{ opacity: 0, scale: 0.95 }}
    animate={{ opacity: 1, scale: 1 }}
    transition={{ duration: 0.6, ease: [0.25, 0.46, 0.45, 0.94] }}
  >
    <div className="flex w-full flex-col border-b border-gray-200 bg-white p-4 md:w-64 md:border-r md:border-b-0">
      <div className="mb-6 flex items-center gap-2 p-2">
        <GoogleLogo
          src="https://upload.wikimedia.org/wikipedia/commons/thumb/a/a5/Google_Calendar_icon_%282020%29.svg/640px-Google_Calendar_icon_%282020%29.svg.png"
          alt="Google Calendar"
          className="h-8 w-8"
        />
        <span className="text-xl font-semibold text-gray-700">Calendar</span>
      </div>
      <div className="text-center">
        <div className="mb-2 font-semibold text-gray-800">
          {content.month} {content.year}
        </div>
        <div className="mb-2 grid grid-cols-7 gap-1 text-xs text-gray-500">
          {["S", "M", "T", "W", "T", "F", "S"].map((d, index) => (
            <div key={`day-${index}`}>{d}</div>
          ))}
        </div>
        <div className="grid grid-cols-7 gap-1 text-sm">
          {Array.from({ length: 5 }).map((_, i) => (
            <div key={`empty-${i}`} />
          ))}
          {Array.from({ length: 31 }, (_, i) => (
            <div
              key={i}
              className={`flex aspect-square cursor-pointer items-center justify-center rounded-full p-1 transition-colors duration-200 ${i + 1 === content.dueDay ? "bg-blue-600 font-bold text-white" : "text-gray-700 hover:bg-gray-100"}`}
            >
              {i + 1}
            </div>
          ))}
        </div>
      </div>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{
          opacity: 1,
          transition: {
            delay: 1.0,
            duration: 0.5,
            ease: [0.25, 0.46, 0.45, 0.94],
          },
        }}
        className="mt-auto flex items-center gap-2 rounded-lg bg-blue-100 p-2 text-sm text-blue-700"
      >
        <Check className="h-4 w-4" />
        <span>Deadline added to calendar</span>
      </motion.div>
    </div>
    <div className="flex-1 bg-white p-6">
      <div className="mb-4 flex items-baseline justify-between">
        <h2 className="text-xl font-normal text-gray-700 md:text-2xl">
          <span className="font-bold text-blue-600">{content.dayOfWeek},</span>{" "}
          {content.month} {content.dueDay}
        </h2>
        <div className="text-sm text-gray-500">Day</div>
      </div>
      <div className="relative h-full">
        <div className="absolute inset-0 grid grid-cols-1 grid-rows-12">
          {Array.from({ length: 12 }).map((_, i) => (
            <div key={i} className="border-t border-gray-200" />
          ))}
        </div>
        <motion.div
          initial={{ opacity: 0, y: 30, scale: 0.9 }}
          animate={{
            opacity: 1,
            y: 0,
            scale: 1,
            transition: {
              delay: 0.4,
              duration: 0.8,
              ease: [0.25, 0.46, 0.45, 0.94],
            },
          }}
          className="absolute top-[60.33%] right-4 left-4 flex h-20 items-start gap-4 rounded-lg border-l-4 border-blue-500 bg-blue-100 p-3 shadow-lg"
        >
          <div className="flex-1">
            <h3 className="text-sm font-semibold text-blue-900">
              {emailContent.subject}
            </h3>
            <p className="text-xs text-blue-800">{emailContent.topic}</p>
          </div>
          <div className="flex items-center gap-2 text-xs text-blue-800">
            <Clock className="h-3 w-3" />
            <span>11:59 PM</span>
          </div>
        </motion.div>
      </div>
    </div>
  </motion.div>
);

const SlidesView: React.FC<{
  content: DemoData["slides"];
  emailContent: DemoData["email"];
  onComplete: () => void;
}> = ({ content, emailContent, onComplete }) => {
  const [currentSlideIndex, setCurrentSlideIndex] = useState(0);

  useEffect(() => {
    if (currentSlideIndex >= content.length - 1) {
      const finalTimer = setTimeout(onComplete, 1200);
      return () => clearTimeout(finalTimer);
    }

    const timer = setTimeout(() => {
      setCurrentSlideIndex((prev) => prev + 1);
    }, 1200);

    return () => clearTimeout(timer);
  }, [currentSlideIndex, content.length, onComplete]);

  const currentSlide = content[currentSlideIndex];

  type ToolbarIconProps = {
    icon: ElementType;
    active?: boolean;
    hasDropdown?: boolean;
  };

  const ToolbarIcon: React.FC<ToolbarIconProps> = ({
    icon: Icon,
    active = false,
    hasDropdown = false,
  }) => (
    <button
      className={`rounded p-1.5 transition-colors duration-200 hover:bg-gray-200 ${active ? "bg-blue-100 text-blue-600" : "text-gray-600"}`}
    >
      <div className="flex items-center">
        <Icon className="h-5 w-5" />
        {hasDropdown && <ChevronDown className="ml-0.5 h-3 w-3" />}
      </div>
    </button>
  );

  return (
    <motion.div
      layoutId="main-container"
      className="flex h-[600px] w-full max-w-7xl flex-col overflow-hidden rounded-2xl bg-[#F8F9FA] shadow-2xl"
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.6, ease: [0.25, 0.46, 0.45, 0.94] }}
    >
      <div className="border-b border-gray-300 bg-white px-2 py-1 text-sm text-gray-800">
        <div className="flex items-center gap-3">
          <GoogleLogo
            src="https://upload.wikimedia.org/wikipedia/commons/thumb/1/16/Google_Slides_2020_Logo.svg/640px-Google_Slides_2020_Logo.svg.png"
            alt="Google Slides"
            className="h-8 w-8 flex-shrink-0"
          />
          <div className="flex min-w-0 flex-grow flex-col">
            <span className="truncate font-medium">{emailContent.topic}</span>
            <div className="mt-1 flex items-center gap-4 text-xs text-gray-600">
              <Star className="h-4 w-4 cursor-pointer text-gray-500 transition-colors duration-200 hover:text-yellow-500" />
              <span className="cursor-pointer rounded px-1 py-0.5 transition-colors duration-200 hover:bg-gray-100">
                File
              </span>
              <span className="cursor-pointer rounded px-1 py-0.5 transition-colors duration-200 hover:bg-gray-100">
                Edit
              </span>
              <span className="cursor-pointer rounded px-1 py-0.5 transition-colors duration-200 hover:bg-gray-100">
                View
              </span>
            </div>
          </div>
          <div className="ml-auto flex flex-shrink-0 items-center gap-3">
            <motion.div
              initial={{ opacity: 0 }}
              animate={{
                opacity: 1,
                transition: {
                  delay: 0.5,
                  duration: 0.5,
                  ease: [0.25, 0.46, 0.45, 0.94],
                },
              }}
              className="hidden items-center gap-2 rounded-full bg-green-100 px-3 py-1 md:flex"
            >
              <Zap className="h-4 w-4 text-green-700" />
              <span className="text-xs font-medium text-green-800">
                Draft by GAIA
              </span>
            </motion.div>
            <button className="rounded-md bg-[#1A73E8] px-4 py-2 text-sm font-semibold text-white transition-colors duration-200 hover:bg-[#1557B0]">
              Share
            </button>
          </div>
        </div>
      </div>

      <div className="flex flex-shrink-0 items-center gap-1 border-b border-gray-200 bg-white px-3 py-1">
        <ToolbarIcon icon={MousePointer2} active />
        <ToolbarIcon icon={Type} />
        <ToolbarIcon icon={ImageIcon} />
        <div className="mx-1 h-6 w-px bg-gray-300"></div>
        <div className="flex items-center gap-1">
          <button className="rounded px-2 py-1 text-sm transition-colors duration-200 hover:bg-gray-100">
            Background
          </button>
          <button className="flex items-center gap-1 rounded px-2 py-1 text-sm transition-colors duration-200 hover:bg-gray-100">
            Layout <ChevronDown className="h-4 w-4" />
          </button>
        </div>
      </div>

      <div className="flex flex-1 overflow-hidden bg-[#E9EEF6]">
        <div className="w-40 space-y-2 overflow-y-auto border-r border-gray-200 bg-white p-3">
          {content.map((slide, i) => (
            <div
              key={i}
              className="group relative cursor-pointer rounded-sm p-1"
            >
              <span className="absolute top-1 left-2 z-10 text-xs text-gray-500">
                {i + 1}
              </span>
              {i === currentSlideIndex && (
                <motion.div
                  layoutId="active-slide-indicator"
                  className="absolute inset-0 rounded-sm border-2 border-blue-500"
                  transition={{ type: "spring", stiffness: 400, damping: 30 }}
                />
              )}
              <div
                className={`relative flex aspect-video items-center justify-center rounded-sm border border-gray-400 bg-white p-1 transition-colors duration-200 ${i !== currentSlideIndex ? "group-hover:border-gray-500" : ""}`}
              >
                <p className="px-1 text-center text-[8px] font-semibold text-gray-600">
                  {slide.title}
                </p>
              </div>
            </div>
          ))}
        </div>

        <div className="flex flex-1 flex-col">
          <div className="flex flex-1 overflow-hidden">
            <div className="flex flex-1 items-center justify-center p-8">
              <AnimatePresence mode="wait">
                <motion.div
                  key={currentSlideIndex}
                  initial={{ opacity: 0, scale: 0.95 }}
                  animate={{
                    opacity: 1,
                    scale: 1,
                    transition: {
                      duration: 0.6,
                      ease: [0.25, 0.46, 0.45, 0.94],
                    },
                  }}
                  exit={{
                    opacity: 0,
                    scale: 0.95,
                    transition: {
                      duration: 0.3,
                      ease: [0.25, 0.46, 0.45, 0.94],
                    },
                  }}
                  className={`flex h-full w-full flex-col justify-between rounded-sm border border-gray-300 p-8 text-left shadow-lg ${currentSlide.bgColor} ${currentSlide.textColor}`}
                >
                  <div>
                    <h1
                      className={`mb-4 text-3xl font-bold md:text-4xl ${currentSlide.highlightColor}`}
                    >
                      {currentSlide.title}
                    </h1>
                    {currentSlide.subtitle && (
                      <p className="text-lg opacity-80 md:text-xl">
                        {currentSlide.subtitle}
                      </p>
                    )}
                    {currentSlide.points && (
                      <ul className="mt-6 space-y-3 text-sm md:text-base">
                        {currentSlide.points.map((point, i) => (
                          <motion.li
                            key={i}
                            className="flex items-start gap-3"
                            initial={{ opacity: 0, x: -20 }}
                            animate={{
                              opacity: 1,
                              x: 0,
                              transition: {
                                delay: 0.3 + i * 0.1,
                                duration: 0.5,
                                ease: [0.25, 0.46, 0.45, 0.94],
                              },
                            }}
                          >
                            <ArrowRight
                              className={`mt-1 h-5 w-5 flex-shrink-0 ${currentSlide.highlightColor}`}
                            />
                            <span>{point}</span>
                          </motion.li>
                        ))}
                      </ul>
                    )}
                  </div>
                  <div className="mt-auto text-right text-xs opacity-60">
                    Slide {currentSlideIndex + 1} of {content.length}
                  </div>
                </motion.div>
              </AnimatePresence>
            </div>
          </div>
        </div>
      </div>
      {currentSlideIndex === content.length - 1 && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{
            opacity: 1,
            transition: {
              delay: 0.5,
              duration: 0.5,
              ease: [0.25, 0.46, 0.45, 0.94],
            },
          }}
          className="absolute bottom-4 left-1/2 flex -translate-x-1/2 items-center gap-2 rounded-lg bg-green-100 p-2 text-sm text-green-700 shadow-md"
        >
          <Check className="h-4 w-4" />
          <span>Presentation draft complete</span>
        </motion.div>
      )}
    </motion.div>
  );
};

// 👇 UPDATED: Custom Node Component with larger text and nodes
const CustomNode: React.FC<NodeProps> = ({ data }) => {
  const { label, time, icon: Icon, isCompleted, isCurrent, index } = data;

  const isEven = index % 2 === 0;

  const stateClasses = isCompleted
    ? "bg-[#01BBFF] border-[#01BBFF] text-white shadow-md"
    : isCurrent
      ? "bg-white border-[#01BBFF] text-gray-900 shadow-lg scale-[1.03]"
      : "bg-white border-gray-200 text-gray-900 shadow-sm";

  const iconContainerClasses = `w-12 h-12 rounded-md flex items-center justify-center flex-shrink-0 mr-5 transition-colors duration-150 ${
    isCompleted ? "bg-white/20" : "bg-gray-100 text-[#01BBFF]"
  }`;

  return (
    <div
      className={`flex ${isEven ? "flex-row" : "flex-row-reverse"} w-[360px] items-center rounded-xl border-2 p-5 transition-all duration-150 ${stateClasses}`}
    >
      <Handle type="target" position={Position.Left} className="!opacity-0" />
      <Handle type="source" position={Position.Right} className="!opacity-0" />

      <div className={iconContainerClasses}>
        {isCompleted ? (
          <Check className="h-6 w-6 text-white" />
        ) : (
          <Icon className="h-6 w-6" />
        )}
      </div>
      <div className="flex-1 text-left">
        <h4 className="text-lg leading-snug font-semibold">{label}</h4>
        <p
          className={`text-base ${isCompleted ? "text-white/80" : "text-gray-500"}`}
        >
          {time}
        </p>
      </div>
    </div>
  );
};

const RoadmapView: React.FC<{
  currentStep: number;
  content: DemoData["roadmap"];
  emailContent: DemoData["email"];
  onComplete: () => void;
}> = ({ currentStep, content, emailContent, onComplete }) => {
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);

  const { initialNodes, initialEdges } = useMemo(() => {
    const spacingX = 280;
    const offsetY = 160;

    const initialNodes: Node[] = content.map((step, index) => ({
      id: `step-${index}`,
      type: "custom",
      position: {
        x: index * spacingX - 100,
        y: index % 2 === 0 ? 100 : 100 + offsetY,
      },
      data: {
        label: step.label,
        time: step.time,
        icon: step.icon,
        isCompleted: currentStep > index,
        isCurrent: currentStep === index,
        index,
      },
    }));

    const initialEdges: Edge[] = content.slice(0, -1).map((_, index) => ({
      id: `edge-${index}`,
      source: `step-${index}`,
      target: `step-${index + 1}`,
      type: "smoothstep",
      animated: currentStep > index,
      style: {
        strokeWidth: 2,
        stroke: currentStep > index ? "#01BBFF" : "#E5E7EB",
        strokeDasharray: currentStep > index ? "3 3" : undefined,
        animated: true,
      },
      markerEnd: {
        type: MarkerType.ArrowClosed,
        color: currentStep > index ? "#01BBFF" : "#E5E7EB",
        width: 12,
        height: 12,
      },
    }));

    return { initialNodes, initialEdges };
  }, [content, currentStep]);

  useEffect(() => {
    setNodes(initialNodes);
    setEdges(initialEdges);
  }, [initialNodes, initialEdges, setNodes, setEdges]);

  useEffect(() => {
    if (currentStep >= content.length) {
      const timer = setTimeout(onComplete, 100);
      return () => clearTimeout(timer);
    }
  }, [currentStep, content.length, onComplete]);

  const nodeTypes = useMemo(() => ({ custom: CustomNode }), []);

  return (
    <div className="flex h-[500px] w-full max-w-full flex-col overflow-hidden rounded-2xl bg-white">
      <div className="border-b border-gray-200 px-6 py-4">
        <div className="flex items-center gap-4">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-[#01BBFF]">
            <Target className="h-6 w-6 text-white" />
          </div>
          <div>
            <h2 className="text-xl font-semibold text-gray-900">
              {emailContent.topic}
            </h2>
            <p className="text-base text-gray-500">Project Action Plan</p>
          </div>
        </div>
      </div>

      <div className="h-full w-full flex-1">
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          nodeTypes={nodeTypes}
          fitView
          fitViewOptions={{ padding: 0.1 }}
          nodesDraggable={false}
          nodesConnectable={false}
          elementsSelectable={false}
          panOnDrag={false}
          zoomOnScroll={false}
          zoomOnPinch={false}
        />
      </div>
    </div>
  );
};

const StageDescriptions: React.FC<{ stage: string }> = ({ stage }) => {
  const descriptions = {
    gmail: { icon: Mail, text: "Processing email", color: "text-primary" },
    calendar: {
      icon: Calendar,
      text: "Scheduling event",
      color: "text-primary",
    },
    slides: {
      icon: FileText,
      text: "Creating presentation",
      color: "text-primary",
    },
    roadmap: { icon: Target, text: "Building roadmap", color: "text-primary" },
    completed: {
      icon: CheckCircle,
      text: "Task completed",
      color: "text-primary",
    },
  };

  const current = descriptions[stage as keyof typeof descriptions];
  if (!current) return null;

  return (
    <div className="fixed top-8 left-1/2 z-50 -translate-x-1/2 transform">
      <motion.div
        layout
        className="overflow-hidden rounded-full border border-white/20 bg-black/95 px-4 py-3 text-white shadow-2xl backdrop-blur-xl"
        transition={{
          type: "spring",
          stiffness: 500,
          damping: 40,
          mass: 0.5,
        }}
      >
        <AnimatePresence mode="wait">
          <motion.div
            key={stage}
            initial={{ opacity: 0, filter: "blur(4px)", x: 10 }}
            animate={{ opacity: 1, filter: "blur(0px)", x: 0 }}
            exit={{ opacity: 0, filter: "blur(4px)", x: -10 }}
            transition={{
              type: "spring",
              stiffness: 600,
              damping: 45,
              mass: 0.3,
            }}
            className="flex items-center gap-3"
          >
            <motion.div
              initial={{ scale: 0.8, rotate: -90 }}
              animate={{ scale: 1, rotate: 0 }}
              exit={{ scale: 0.8, rotate: 90 }}
              transition={{
                type: "spring",
                stiffness: 700,
                damping: 35,
                mass: 0.2,
              }}
            >
              <current.icon
                className={`h-4 w-4 ${current.color} flex-shrink-0`}
              />
            </motion.div>

            <motion.span
              className="text-sm font-medium whitespace-nowrap"
              initial={{ opacity: 0, y: 5 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -5 }}
              transition={{
                delay: 0.05,
                type: "spring",
                stiffness: 800,
                damping: 50,
              }}
            >
              {current.text}
            </motion.span>

            {stage !== "completed" && (
              <motion.div
                className="ml-1 flex space-x-1"
                initial={{ opacity: 0, scale: 0.5 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.5 }}
                transition={{
                  delay: 0.1,
                  type: "spring",
                  stiffness: 600,
                  damping: 40,
                }}
              >
                <div
                  className="h-1 w-1 animate-pulse rounded-full bg-white/60"
                  style={{ animationDelay: "0s" }}
                ></div>
                <div
                  className="h-1 w-1 animate-pulse rounded-full bg-white/60"
                  style={{ animationDelay: "0.2s" }}
                ></div>
                <div
                  className="h-1 w-1 animate-pulse rounded-full bg-white/60"
                  style={{ animationDelay: "0.4s" }}
                ></div>
              </motion.div>
            )}
          </motion.div>
        </AnimatePresence>
      </motion.div>
    </div>
  );
};

const ProactiveDemo: React.FC = () => {
  const { ref, inView } = useInView({
    triggerOnce: true,
    threshold: 0.4,
  });

  const [stage, setStage] = useState("gmail");
  const [isExpanded, setIsExpanded] = useState(false);
  const [highlightTrigger, setHighlightTrigger] = useState(false);
  const [roadmapStep, setRoadmapStep] = useState(-1);
  const [contentIndex, setContentIndex] = useState(0);
  const [showCompleted, setShowCompleted] = useState(false);
  const isMounted = useRef(true);

  const currentContent = demoContents[contentIndex];
  const totalRoadmapSteps = currentContent.roadmap.length;

  const animationSequence = useCallback(async () => {
    if (!isMounted.current) return;

    setStage("gmail");
    setIsExpanded(false);
    setHighlightTrigger(false);
    setRoadmapStep(-1);
    setShowCompleted(false);
    await wait(1000);

    if (!isMounted.current) return;
    setIsExpanded(true);
    await wait(800);

    if (!isMounted.current) return;
    setHighlightTrigger(true);
    await wait(1500);

    if (!isMounted.current) return;
    setStage("calendar");
    await wait(2000);

    if (!isMounted.current) return;
    setStage("slides");
  }, [contentIndex]);

  const handleSlidesComplete = useCallback(async () => {
    if (!isMounted.current) return;
    setStage("roadmap");
    await wait(400);

    for (let i = 0; i <= totalRoadmapSteps; i++) {
      if (!isMounted.current) return;
      setRoadmapStep(i);
      await wait(500);
    }
  }, [totalRoadmapSteps]);

  const handleRoadmapComplete = useCallback(async () => {
    if (!isMounted.current) return;
    setStage("completed");
    setShowCompleted(true);
    await wait(1500);

    if (isMounted.current) {
      setContentIndex((prev) => (prev + 1) % demoContents.length);
      const timer = setTimeout(animationSequence, 800);
      return () => clearTimeout(timer);
    }
  }, [animationSequence, demoContents.length]);

  useEffect(() => {
    isMounted.current = true;
    let timer: NodeJS.Timeout | undefined;

    if (inView) {
      timer = setTimeout(animationSequence, 800);
    }

    return () => {
      isMounted.current = false;
      if (timer) {
        clearTimeout(timer);
      }
    };
  }, [inView, animationSequence]);

  return (
    <div
      ref={ref}
      className="anim-container relative flex h-[650px] w-full max-w-7xl items-center justify-center overflow-hidden rounded-3xl border border-white/10 bg-gradient-to-br from-white/[0.02] to-transparent p-4 shadow-2xl shadow-black/40 backdrop-blur-2xl md:p-8"
    >
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_30%_40%,rgba(1,187,255,0.1),transparent_50%)]" />
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_70%_60%,rgba(6,182,212,0.1),transparent_50%)]" />

      <AnimatePresence mode="wait">
        {stage === "gmail" && (
          <GmailView
            key="gmail"
            isExpanded={isExpanded}
            highlightTrigger={highlightTrigger}
            content={currentContent.email}
          />
        )}
        {stage === "calendar" && (
          <CalendarView
            key="calendar"
            content={currentContent.calendar}
            emailContent={currentContent.email}
          />
        )}
        {stage === "slides" && (
          <SlidesView
            key="slides"
            content={currentContent.slides}
            emailContent={currentContent.email}
            onComplete={handleSlidesComplete}
          />
        )}
        {stage === "roadmap" && (
          <RoadmapView
            key="roadmap"
            currentStep={roadmapStep}
            content={currentContent.roadmap}
            emailContent={currentContent.email}
            onComplete={handleRoadmapComplete}
          />
        )}
        {showCompleted && (
          <motion.div
            key="completed"
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.8 }}
            transition={{ duration: 0.6, ease: [0.25, 0.46, 0.45, 0.94] }}
            className="flex flex-col items-center justify-center gap-6 text-center"
          >
            <motion.div
              className="flex h-20 w-20 items-center justify-center rounded-full bg-green-100"
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              transition={{
                delay: 0.2,
                type: "spring",
                stiffness: 300,
                damping: 25,
              }}
            >
              <CheckCircle className="h-10 w-10 text-green-600" />
            </motion.div>
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{
                delay: 0.4,
                duration: 0.6,
                ease: [0.25, 0.46, 0.45, 0.94],
              }}
            >
              <h3 className="mb-2 text-2xl font-bold text-white">
                Task Completed Successfully
              </h3>
              <p className="text-gray-300">
                GAIA has handled everything automatically
              </p>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      <AnimatePresence>
        <StageDescriptions
          key={stage}
          stage={showCompleted ? "completed" : stage}
        />
      </AnimatePresence>
    </div>
  );
};

export default function Proactive() {
  return (
    <div className="bg-grid-white/[0.05] relative min-h-screen w-full overflow-x-hidden bg-[radial-gradient(ellipse_at_top_left,_#0f0f0f,_#09090b)] bg-cover bg-fixed bg-no-repeat">
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_50%_50%,rgba(1,187,255,0.05),transparent_50%)]" />
      <div className="absolute inset-0 bg-[linear-gradient(to_right,#80808008_1px,transparent_1px),linear-gradient(to_bottom,#80808008_1px,transparent_1px)] bg-[size:32px_32px]" />

      <div className="relative z-10 container mx-auto flex min-h-screen max-w-7xl flex-col items-center justify-center gap-12 px-4 py-12 sm:py-16 md:gap-16 md:py-24">
        <LargeHeader
          headingText="An Assistant That Acts Before You Ask"
          subHeadingText="GAIA intelligently handles emails, schedules, presentations, and tasks so you can focus on what truly matters."
        />
        <ProactiveDemo />
      </div>
    </div>
  );
}
