import "reactflow/dist/style.css";

import {
  CheckCircle,
  Clock,
  GitBranch,
  Send,
  Target,
  TargetIcon,
} from "lucide-react";
import React, { useCallback, useEffect, useRef, useState } from "react";
import ReactFlow, {
  Background,
  Edge,
  Handle,
  MarkerType,
  Node,
  Position,
  useEdgesState,
  useNodesState,
} from "reactflow";

import { Target02Icon } from "@/components";

import SectionChip from "../../shared/SectionChip";

// Helper to wait for a specific duration
const wait = (ms: number): Promise<void> =>
  new Promise((resolve) => setTimeout(resolve, ms));

// --- Step Definitions ---
interface Step {
  icon: React.ReactNode;
  title: string;
  description: string;
  demo: "chat" | "roadmap" | "tracking";
}

const steps: Step[] = [
  {
    icon: <Target02Icon className="h-5 w-5" color={undefined} />,
    title: "Enter your goal",
    description:
      "Define your objective clearly so we can create a personalized plan for you.",
    demo: "chat",
  },
  {
    icon: <GitBranch className="h-5 w-5" />,
    title: "Create a Roadmap",
    description:
      "Our AI provides a step-by-step plan to help you achieve your goal!",
    demo: "roadmap",
  },
  {
    icon: <CheckCircle className="h-5 w-5" />,
    title: "Keep Track",
    description:
      "Monitor your milestones and celebrate every step toward achieving your goal.",
    demo: "tracking",
  },
];

// --- Message Interface for Chat ---
interface Message {
  type: "user" | "ai";
  text: string;
}

// --- Chat Demo Component ---
const ChatDemo: React.FC<{ isActive: boolean }> = ({ isActive }) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [typingText, setTypingText] = useState("");
  const [isAiTyping, setIsAiTyping] = useState(false);
  const [showCursor, setShowCursor] = useState(false);
  const [_animationComplete, setAnimationComplete] = useState(false);

  const isMounted = useRef(true);
  const timeoutRef = useRef<NodeJS.Timeout | null>(null);

  const runAnimation = useCallback(async () => {
    if (!isMounted.current || !isActive) return;

    const fullText = "I want to learn React in 3 months";

    // Reset state
    setMessages([]);
    setTypingText("");
    setIsAiTyping(false);
    setShowCursor(false);
    setAnimationComplete(false);

    await wait(800);
    if (!isMounted.current || !isActive) return;

    // Type out the user message
    setShowCursor(true);
    for (let i = 0; i <= fullText.length; i++) {
      if (!isMounted.current || !isActive) return;
      setTypingText(fullText.substring(0, i));
      await wait(60);
    }

    if (!isMounted.current || !isActive) return;
    setShowCursor(false);
    await wait(800);

    if (!isMounted.current || !isActive) return;
    setMessages([{ type: "user", text: fullText }]);
    setTypingText("");

    await wait(800);
    if (!isMounted.current || !isActive) return;
    setIsAiTyping(true);

    await wait(2000);
    if (!isMounted.current || !isActive) return;
    setIsAiTyping(false);
    setMessages((prev) => [
      ...prev,
      {
        type: "ai",
        text: "Perfect! I'll create a personalized React learning roadmap for you.",
      },
    ]);

    await wait(1500);
    if (!isMounted.current || !isActive) return;
    setAnimationComplete(true);
  }, [isActive]);

  useEffect(() => {
    isMounted.current = true;

    if (isActive) {
      timeoutRef.current = setTimeout(runAnimation, 500);
    } else {
      setMessages([]);
      setTypingText("");
      setIsAiTyping(false);
      setShowCursor(false);
      setAnimationComplete(false);
    }

    return () => {
      isMounted.current = false;
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, [isActive, runAnimation]);

  return (
    <div className="flex h-full w-full flex-col rounded-2xl border border-white/5 bg-gradient-to-br from-white/[0.02] to-transparent p-6 backdrop-blur-sm">
      <div className="mb-6 flex min-h-[180px] flex-1 flex-col justify-center space-y-4">
        {messages.map((message, index) => (
          <div
            key={index}
            className={`flex ${message.type === "user" ? "justify-end" : "justify-start"} duration-500 animate-in fade-in-0 slide-in-from-bottom-4`}
          >
            <div
              className={`max-w-[85%] rounded-2xl px-4 py-3 text-sm transition-all duration-300 ${
                message.type === "user"
                  ? "bg-[#01BBFF] text-white shadow-lg shadow-[#01BBFF]/10"
                  : "border border-white/10 bg-slate-800/50 text-white"
              }`}
            >
              {message.text}
            </div>
          </div>
        ))}
        {isAiTyping && (
          <div className="flex justify-start duration-300 animate-in fade-in-0 slide-in-from-bottom-4">
            <div className="rounded-2xl border border-white/10 bg-slate-800/50 px-4 py-3">
              <div className="flex space-x-1">
                <div className="h-2 w-2 animate-bounce rounded-full bg-[#01BBFF]"></div>
                <div
                  className="h-2 w-2 animate-bounce rounded-full bg-[#01BBFF]"
                  style={{ animationDelay: "0.15s" }}
                ></div>
                <div
                  className="h-2 w-2 animate-bounce rounded-full bg-[#01BBFF]"
                  style={{ animationDelay: "0.3s" }}
                ></div>
              </div>
            </div>
          </div>
        )}
        {!messages.length && !isAiTyping && (
          <div className="flex h-full items-center justify-center text-sm text-gray-400">
            Waiting for your goal...
          </div>
        )}
      </div>

      <div className="flex items-center gap-2 rounded-xl border border-white/10 bg-slate-800/30 p-3 transition-all duration-300">
        <div className="h-6 flex-1 bg-transparent px-2 py-1 text-sm text-white placeholder-gray-400 outline-none">
          {typingText}
          {showCursor && (
            <span className="ml-px inline-block h-4 w-px animate-pulse bg-[#01BBFF]"></span>
          )}
        </div>
        <button
          className="rounded-lg bg-[#01BBFF] p-2 text-white transition-all duration-200 hover:scale-105 hover:bg-[#01BBFF]/80 active:scale-95"
          aria-label="Send message"
        >
          <Send className="h-4 w-4" />
        </button>
      </div>
    </div>
  );
};

// --- Roadmap Demo Component ---
interface CustomNodeData {
  label: string;
  isActive: boolean;
}

interface CustomNodeProps {
  data: CustomNodeData;
}

const CustomNode = ({ data }: CustomNodeProps) => {
  return (
    <div
      className={`min-w-[120px] rounded-xl border-2 px-4 py-3 text-center text-sm font-medium transition-all duration-300 ${
        data.isActive
          ? "border-[#01BBFF] bg-[#01BBFF]/10 text-[#01BBFF] shadow-lg shadow-[#01BBFF]/10"
          : "border-gray-600/0 bg-slate-800/0 text-gray-400/0"
      }`}
    >
      {/* Target Handle (for incoming edges) */}
      <Handle
        type="target"
        position={Position.Left}
        className="!border-0 !bg-transparent"
      />

      <div className="font-semibold">{data.label}</div>

      {/* Source Handle (for outgoing edges) */}
      <Handle
        type="source"
        position={Position.Right}
        className="!border-0 !bg-transparent"
      />
    </div>
  );
};

const nodeTypes = {
  custom: CustomNode,
};

// --- Roadmap Demo Component ---
// --- Roadmap Demo Component ---
const RoadmapDemo: React.FC<{ isActive: boolean }> = ({ isActive }) => {
  const isMounted = useRef(true);
  const timeoutRef = useRef<NodeJS.Timeout | null>(null);

  // --- Initial State Definitions ---
  const initialNodes: Node[] = [
    {
      id: "1",
      type: "custom",
      position: { x: 0, y: 100 },
      data: { label: "Learn Fundamentals", isActive: false },
    },
    {
      id: "2",
      type: "custom",
      position: { x: 280, y: 30 },
      data: { label: "Build Projects", isActive: false },
    },
    {
      id: "3",
      type: "custom",
      position: { x: 280, y: 170 },
      data: { label: "Master Advanced", isActive: false },
    },
  ];

  const initialEdges: Edge[] = [
    {
      id: "e1-2",
      source: "1",
      target: "2",
      type: "bezier",
      animated: false,
      style: { stroke: "#6B728000", strokeWidth: 1, strokeOpacity: 0.6 },
      markerEnd: {
        type: MarkerType.ArrowClosed,
        color: "#6B728000",
        width: 15,
        height: 15,
      },
    },
    {
      id: "e1-3",
      source: "1",
      target: "3",
      type: "bezier",
      animated: false,
      style: { stroke: "#6B728000", strokeWidth: 1, strokeOpacity: 0.6 },
      markerEnd: {
        type: MarkerType.ArrowClosed,
        color: "#6B728000",
        width: 15,
        height: 15,
      },
    },
  ];

  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);

  // --- Staggered Animation Logic ---
  const runAnimation = useCallback(async () => {
    if (!isMounted.current || !isActive) return;

    // 1. Reset to initial state
    setNodes(
      initialNodes.map((n) => ({ ...n, data: { ...n.data, isActive: false } })),
    );
    setEdges(initialEdges);

    await wait(50);
    if (!isMounted.current || !isActive) return;

    // 2. Activate first node
    setNodes((currentNodes) =>
      currentNodes.map((n) =>
        n.id === "1" ? { ...n, data: { ...n.data, isActive: true } } : n,
      ),
    );

    await wait(50);
    if (!isMounted.current || !isActive) return;

    // 3. Animate first edge, then activate the connected node
    setEdges((currentEdges) =>
      currentEdges.map((e) =>
        e.id === "e1-2"
          ? {
              ...e,
              animated: true,
              style: { stroke: "#01BBFF", strokeWidth: 1.5 },
              // ✅ FIX: Construct a new object instead of spreading a potentially non-object type
              markerEnd: {
                type: MarkerType.ArrowClosed,
                color: "#01BBFF",
                width: 18,
                height: 18,
              },
            }
          : e,
      ),
    );

    await wait(50);
    if (!isMounted.current || !isActive) return;
    setNodes((currentNodes) =>
      currentNodes.map((n) =>
        n.id === "2" ? { ...n, data: { ...n.data, isActive: true } } : n,
      ),
    );

    await wait(50);
    if (!isMounted.current || !isActive) return;

    // 4. Animate second edge, then activate its connected node
    setEdges((currentEdges) =>
      currentEdges.map((e) =>
        e.id === "e1-3"
          ? {
              ...e,
              animated: true,
              style: { stroke: "#01BBFF", strokeWidth: 2.5 },
              // ✅ FIX: Construct a new object instead of spreading a potentially non-object type
              markerEnd: {
                type: MarkerType.ArrowClosed,
                color: "#01BBFF",
                width: 18,
                height: 18,
              },
            }
          : e,
      ),
    );

    await wait(50);
    if (!isMounted.current || !isActive) return;
    setNodes((currentNodes) =>
      currentNodes.map((n) =>
        n.id === "3" ? { ...n, data: { ...n.data, isActive: true } } : n,
      ),
    );

    // 5. Wait and loop
    await wait(3500);
    if (isMounted.current && isActive) {
      runAnimation();
    }
  }, [isActive, setNodes, setEdges]);

  // --- Component Lifecycle ---
  useEffect(() => {
    isMounted.current = true;
    if (isActive) {
      timeoutRef.current = setTimeout(runAnimation, 300);
    } else {
      setNodes(initialNodes);
      setEdges(initialEdges);
    }
    return () => {
      isMounted.current = false;
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, [isActive, runAnimation]);

  return (
    <div className="flex h-full w-full flex-col rounded-2xl border border-white/5 bg-gradient-to-br from-white/[0.02] to-transparent p-6 backdrop-blur-sm">
      <div className="mb-6 flex items-center gap-2">
        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-[#01BBFF]">
          <Target className="h-4 w-4 text-white" />
        </div>
        <div>
          <h3 className="text-sm font-semibold text-white">
            Learn React Roadmap
          </h3>
          <p className="text-xs text-gray-400">
            Your personalized learning path
          </p>
        </div>
      </div>

      <div className="relative flex-1 bg-transparent">
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          nodeTypes={nodeTypes}
          fitView
          fitViewOptions={{ padding: 0.2 }}
          proOptions={{ hideAttribution: true }}
          nodesDraggable={false}
          nodesConnectable={false}
          elementsSelectable={false}
          panOnDrag={false}
          zoomOnScroll={false}
          zoomOnPinch={false}
          zoomOnDoubleClick={false}
          className="bg-transparent"
        >
          <Background
            gap={20}
            size={1}
            color="#374151"
            className="opacity-20"
          />
        </ReactFlow>
      </div>
    </div>
  );
};

// --- Tracking Demo Component ---
const TrackingDemo: React.FC<{ isActive: boolean }> = ({ isActive }) => {
  const [progress, setProgress] = useState(0);
  const [_animationComplete, setAnimationComplete] = useState(false);

  const isMounted = useRef(true);
  const timeoutRef = useRef<NodeJS.Timeout | null>(null);

  const runAnimation = useCallback(async () => {
    if (!isMounted.current || !isActive) return;

    setProgress(0);
    setAnimationComplete(false);

    await wait(1000);

    // Animate progress smoothly
    for (let i = 0; i <= 65; i++) {
      if (!isMounted.current || !isActive) return;
      setProgress(i);
      await wait(30);
    }

    if (!isMounted.current || !isActive) return;
    setAnimationComplete(true);
  }, [isActive]);

  useEffect(() => {
    isMounted.current = true;

    if (isActive) {
      timeoutRef.current = setTimeout(runAnimation, 500);
    } else {
      setProgress(0);
      setAnimationComplete(false);
    }

    return () => {
      isMounted.current = false;
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, [isActive, runAnimation]);

  return (
    <div className="flex h-full w-full flex-col rounded-2xl border border-white/5 bg-gradient-to-br from-white/[0.02] to-transparent p-6 backdrop-blur-sm">
      <div className="mb-6 flex items-center justify-between">
        <h3 className="text-sm font-semibold text-white">Progress Overview</h3>
        <div className="flex items-center gap-1 text-xs text-gray-400">
          <Clock className="h-3 w-3" />
          <span>Week 6 of 12</span>
        </div>
      </div>

      <div className="flex flex-1 flex-col justify-center space-y-5">
        <div className="rounded-xl border border-white/5 bg-slate-800/30 p-4">
          <div className="mb-3 flex items-center justify-between">
            <span className="text-sm text-white">Overall Progress</span>
            <span className="text-sm font-medium text-[#01BBFF]">
              {progress}%
            </span>
          </div>
          <div className="h-2 w-full rounded-full bg-slate-700">
            <div
              className="h-2 rounded-full bg-gradient-to-r from-[#01BBFF] to-cyan-400 transition-all duration-200 ease-linear"
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>

        <div className="grid grid-cols-3 gap-3">
          <div className="rounded-lg border border-white/5 bg-slate-800/30 p-3 text-center">
            <div className="text-lg font-bold text-green-400">2</div>
            <div className="text-xs text-gray-400">Completed</div>
          </div>
          <div className="rounded-lg border border-white/5 bg-slate-800/30 p-3 text-center">
            <div className="text-lg font-bold text-[#01BBFF]">1</div>
            <div className="text-xs text-gray-400">In Progress</div>
          </div>
          <div className="rounded-lg border border-white/5 bg-slate-800/30 p-3 text-center">
            <div className="text-lg font-bold text-gray-400">8</div>
            <div className="text-xs text-gray-400">Total Tasks</div>
          </div>
        </div>

        <div className="flex items-center gap-2 rounded-lg border border-green-400/20 bg-green-400/10 p-3">
          <CheckCircle className="h-4 w-4 text-green-400" />
          <span className="text-sm text-green-400">
            Milestone: React Fundamentals ✓
          </span>
        </div>
      </div>
    </div>
  );
};

// --- Step Card Component ---
interface StepCardProps {
  step: Step;
  index: number;
  isActive: boolean;
  onClick: () => void;
}

const StepCard: React.FC<StepCardProps> = ({
  step,
  index,
  isActive,
  onClick,
}) => (
  <div
    onClick={onClick}
    className={`relative cursor-pointer overflow-hidden rounded-3xl border p-7 backdrop-blur-sm transition-all duration-300 ${
      isActive
        ? "border-[#00BBFF]/50 bg-gradient-to-br from-white/[0.02] to-transparent shadow-xs shadow-[#01BBFF]/10"
        : "border-white/5 bg-gradient-to-br from-white/[0.02] to-transparent hover:border-white/10"
    }`}
    role="button"
    tabIndex={0}
    onKeyDown={(e) => {
      if (e.key === "Enter" || e.key === " ") {
        e.preventDefault();
        onClick();
      }
    }}
    aria-label={`Step ${index + 1}: ${step.title}`}
  >
    <div className="flex items-start gap-5">
      <div
        className={`relative flex h-14 w-14 flex-shrink-0 items-center justify-center rounded-xl transition-all duration-300 ${
          isActive
            ? "bg-[#00BBFF] text-white"
            : "border border-white/10 bg-slate-800/50 text-gray-400"
        }`}
      >
        {step.icon}
        <div className="absolute -right-1 -bottom-1 flex h-5 w-5 items-center justify-center rounded-full bg-slate-700 text-xs font-bold text-white ring-2 ring-slate-800/80">
          {index + 1}
        </div>
      </div>

      <div className="flex-1 pt-1">
        <h3 className="mb-2 text-lg font-semibold text-white">{step.title}</h3>
        <p className="text-sm leading-relaxed text-gray-400">
          {step.description}
        </p>
      </div>
    </div>
  </div>
);

// --- Main Goals Component ---
const Goals: React.FC = () => {
  const [activeStep, setActiveStep] = useState(0);
  const [isAutoPlaying, setIsAutoPlaying] = useState(true);

  const intervalRef = useRef<NodeJS.Timeout | null>(null);
  const isMounted = useRef(true);

  const switchToNextStep = useCallback(() => {
    if (!isMounted.current || !isAutoPlaying) return;
    setActiveStep((prev) => (prev + 1) % steps.length);
  }, [isAutoPlaying]);

  const handleStepClick = useCallback(
    (index: number) => {
      if (index === activeStep) return;

      setIsAutoPlaying(false);
      setActiveStep(index);

      // Clear current interval
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }

      // Resume auto-play after user interaction
      setTimeout(() => {
        if (isMounted.current) {
          setIsAutoPlaying(true);
        }
      }, 10000);
    },
    [activeStep],
  );

  useEffect(() => {
    isMounted.current = true;

    if (isAutoPlaying) {
      intervalRef.current = setInterval(switchToNextStep, 8000);
    }

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [isAutoPlaying, switchToNextStep]);

  useEffect(() => {
    return () => {
      isMounted.current = false;
    };
  }, []);

  const renderDemo = () => {
    const currentDemo = steps[activeStep].demo;
    return (
      <div className="h-full w-full transition-all duration-500 ease-in-out">
        {currentDemo === "chat" && <ChatDemo isActive={activeStep === 0} />}
        {currentDemo === "roadmap" && (
          <RoadmapDemo isActive={activeStep === 1} />
        )}
        {currentDemo === "tracking" && (
          <TrackingDemo isActive={activeStep === 2} />
        )}
      </div>
    );
  };

  return (
    <div className="relative min-h-screen overflow-hidden bg-[radial-gradient(ellipse_at_top_left,_rgba(15,15,15,0.9),_rgba(9,9,11,1)),linear-gradient(to_bottom,_#0c0c0c,_#0a0a0a)] bg-cover bg-fixed bg-no-repeat">
      {/* Background Effects */}
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_50%_50%,rgba(1,187,255,0.05),transparent_50%)]" />
      <div className="absolute inset-0 bg-[linear-gradient(to_right,#80808008_1px,transparent_1px),linear-gradient(to_bottom,#80808008_1px,transparent_1px)] bg-[size:32px_32px]" />

      <div className="relative z-10 container mx-auto max-w-7xl py-12 sm:py-16">
        {/* Header */}
        <header className="mb-12 text-center">
          <SectionChip icon={TargetIcon} text="Goal Tracking" />

          {/* <h1 className="text-4xl md:text-5xl lg:text-6xl font-bold bg-gradient-to-r from-white via-white to-gray-400 bg-clip-text text-transparent mb-6 leading-tight">
            Ever Felt Stuck Setting&nbsp;
            <span className="bg-gradient-to-r from-[#9ddcff] to-[#5ac8fa] bg-clip-text text-transparent">
              Goals
            </span>
            ?
          </h1> */}

          <div className="relative mb-6">
            <h1 className="relative z-10 bg-gradient-to-r from-white via-white to-gray-400 bg-clip-text text-4xl leading-tight font-bold text-transparent md:text-5xl lg:text-6xl">
              Ever Felt Stuck Setting Goals ?
            </h1>
          </div>

          <p className="mx-auto max-w-3xl text-lg leading-relaxed text-gray-400 md:text-xl">
            Our intelligent platform transforms your ambitions into actionable,
            easy-to-follow roadmaps. Achieve more, with clarity and focus.
          </p>
        </header>

        {/* Main Content */}
        <main className="grid items-start gap-10 lg:grid-cols-2 xl:gap-16">
          {/* Left Side: Demo Section */}
          <div className="order-2 lg:order-1">
            <div className="sticky top-8">
              <div className="rounded-3xl border border-white/5 bg-gradient-to-br from-white/[0.02] to-transparent p-6 shadow-2xl shadow-black/20 backdrop-blur-sm">
                <div className="flex h-[420px] items-center justify-center">
                  {renderDemo()}
                </div>
              </div>
            </div>
          </div>

          {/* Right Side: Steps Section */}
          <div className="order-1 space-y-8 lg:order-2">
            {steps.map((step, index) => (
              <StepCard
                key={index}
                step={step}
                index={index}
                isActive={activeStep === index}
                onClick={() => handleStepClick(index)}
              />
            ))}
          </div>
        </main>
      </div>
    </div>
  );
};

export default Goals;
