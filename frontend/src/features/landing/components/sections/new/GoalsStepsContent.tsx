import { motion } from "framer-motion";
import { useState } from "react";
import {
  Target02Icon,
  FlowchartIcon,
  CheckmarkCircle02Icon,
  PlusSignIcon,
} from "@/components";

interface StepCardProps {
  stepNumber: number;
  title: string;
  helper: string;
  icon: React.ReactNode;
  isActive: boolean;
  onClick: () => void;
}

interface FlowchartNode {
  id: string;
  title: string;
  status: "completed" | "in-progress" | "pending";
  progress?: number;
}

function StepCard({
  stepNumber,
  title,
  helper,
  icon,
  isActive,
  onClick,
}: StepCardProps) {
  return (
    <motion.div
      whileHover={!isActive ? { scale: 1.02 } : {}}
      onClick={onClick}
      className={`flex-1 cursor-pointer rounded-xl p-6 transition-all duration-200 ${
        isActive
          ? "border border-zinc-700 bg-zinc-900 shadow-lg"
          : "bg-zinc-800/50 hover:border hover:border-zinc-700/50"
      } `}
    >
      <div className="flex items-start space-x-3">
        <div
          className={`flex h-7 w-7 items-center justify-center rounded-full text-xs font-medium ${
            isActive ? "bg-[#00bbff] text-white" : "bg-zinc-700 text-zinc-400"
          } `}
        >
          {icon}
        </div>
        <div className="flex-1">
          <h3
            className={`text-sm font-medium ${isActive ? "text-foreground" : "text-foreground-600"} `}
          >
            Step {stepNumber} · {title}
          </h3>
          <p
            className={`mt-1 text-xs ${isActive ? "text-foreground-400" : "text-foreground-500"} `}
          >
            {helper}
          </p>
        </div>
      </div>
    </motion.div>
  );
}

function EmptyStateCanvas() {
  return (
    <div className="flex h-full flex-col items-center justify-center space-y-6">
      <div className="flex h-16 w-16 items-center justify-center rounded-full bg-zinc-800">
        <Target02Icon className="h-8 w-8 text-zinc-500" />
      </div>
      <div className="space-y-4 text-center">
        <h3 className="text-lg font-medium text-foreground">
          Create your first goal
        </h3>
        <div className="flex items-center space-x-3">
          <input
            type="text"
            placeholder="Enter your goal..."
            className="w-80 rounded-lg border border-zinc-700 bg-zinc-800 px-4 py-2 text-sm text-foreground placeholder-zinc-500 focus:border-[#00bbff] focus:outline-none"
          />
          <button className="rounded-lg bg-[#00bbff] px-6 py-2 text-sm font-medium text-white transition-colors hover:bg-[#0099d4]">
            Generate plan
          </button>
        </div>
      </div>
    </div>
  );
}

function FlowchartCanvas() {
  const nodes: FlowchartNode[] = [
    { id: "1", title: "Research market", status: "completed" },
    { id: "2", title: "Create business plan", status: "completed" },
    { id: "3", title: "Secure funding", status: "in-progress", progress: 60 },
    { id: "4", title: "Build MVP", status: "pending" },
    { id: "5", title: "Launch product", status: "pending" },
  ];

  return (
    <div className="flex h-full items-center justify-center p-8">
      <div className="flex items-center space-x-8">
        {nodes.map((node, index) => (
          <div key={node.id} className="flex items-center">
            <div className="group relative cursor-pointer">
              <div className="rounded-lg border border-zinc-700 bg-zinc-800 px-4 py-3 transition-colors hover:border-zinc-600">
                <div className="flex items-center space-x-2">
                  <div className="h-2 w-2 rounded-full bg-[#00bbff]"></div>
                  <span className="text-sm font-medium text-foreground">
                    {node.title}
                  </span>
                </div>
              </div>
              {/* Hover toolbar */}
              <div className="absolute -top-10 left-1/2 -translate-x-1/2 transform opacity-0 transition-opacity group-hover:opacity-100">
                <div className="flex items-center space-x-1 rounded-md border border-zinc-700 bg-zinc-900 px-2 py-1">
                  <button className="text-xs text-zinc-400 hover:text-foreground">
                    Rename
                  </button>
                  <div className="h-3 w-px bg-zinc-700"></div>
                  <button className="text-xs text-zinc-400 hover:text-foreground">
                    Delete
                  </button>
                </div>
              </div>
            </div>
            {index < nodes.length - 1 && (
              <div className="mx-4 flex items-center">
                <div className="h-px w-8 bg-zinc-700"></div>
                <div className="ml-1 h-0 w-0 border-y-2 border-l-4 border-y-transparent border-l-zinc-700"></div>
              </div>
            )}
          </div>
        ))}
        <button className="flex h-10 w-10 items-center justify-center rounded-lg border-2 border-dashed border-zinc-700 text-zinc-500 transition-colors hover:border-zinc-600 hover:text-zinc-400">
          <PlusSignIcon className="h-4 w-4" />
        </button>
      </div>
    </div>
  );
}

function TrackerCanvas() {
  const nodes: FlowchartNode[] = [
    { id: "1", title: "Research market", status: "completed" },
    { id: "2", title: "Create business plan", status: "completed" },
    { id: "3", title: "Secure funding", status: "in-progress", progress: 60 },
    { id: "4", title: "Build MVP", status: "pending" },
    { id: "5", title: "Launch product", status: "pending" },
  ];

  const completedCount = nodes.filter((n) => n.status === "completed").length;
  const totalCount = nodes.length;

  return (
    <div className="h-full p-8">
      {/* Progress header */}
      <div className="mb-8 flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <div className="rounded-lg bg-[#00bbff]/10 px-3 py-1 text-sm font-medium text-[#00bbff]">
            {completedCount}/{totalCount} completed
          </div>
        </div>
        <div className="rounded-lg border border-zinc-700 bg-zinc-800 px-4 py-2">
          <div className="flex items-center space-x-2">
            <div className="h-2 w-2 rounded-full bg-orange-500"></div>
            <span className="text-sm font-medium text-foreground">
              Next: Secure funding
            </span>
          </div>
        </div>
      </div>

      {/* Tracker nodes */}
      <div className="flex items-center justify-center">
        <div className="flex items-center space-x-8">
          {nodes.map((node, index) => (
            <div key={node.id} className="flex items-center">
              <div className="group relative">
                <div
                  className={`rounded-lg border px-4 py-3 transition-colors ${
                    node.status === "completed"
                      ? "border-green-500/50 bg-green-500/10"
                      : node.status === "in-progress"
                        ? "border-orange-500/50 bg-orange-500/10"
                        : "border-zinc-700 bg-zinc-800"
                  } `}
                >
                  <div className="flex items-center space-x-3">
                    {node.status === "completed" ? (
                      <CheckmarkCircle02Icon className="h-4 w-4 text-green-500" />
                    ) : node.status === "in-progress" ? (
                      <div className="relative h-4 w-4">
                        <div className="absolute inset-0 rounded-full border-2 border-zinc-700"></div>
                        <div
                          className="absolute inset-0 animate-spin rounded-full border-2 border-orange-500 border-t-transparent"
                          style={{ animationDuration: "2s" }}
                        ></div>
                      </div>
                    ) : (
                      <div className="h-4 w-4 rounded-full border-2 border-zinc-600"></div>
                    )}
                    <span
                      className={`text-sm font-medium ${node.status === "completed" ? "text-green-400" : "text-foreground"} `}
                    >
                      {node.title}
                    </span>
                    <div
                      className={`rounded-full px-2 py-0.5 text-xs font-medium ${
                        node.status === "completed"
                          ? "bg-green-500/20 text-green-400"
                          : node.status === "in-progress"
                            ? "bg-orange-500/20 text-orange-400"
                            : "bg-zinc-700 text-zinc-400"
                      } `}
                    >
                      {node.status === "completed"
                        ? "Done"
                        : node.status === "in-progress"
                          ? `${node.progress}%`
                          : "Pending"}
                    </div>
                  </div>
                </div>
              </div>
              {index < nodes.length - 1 && (
                <div className="mx-4 flex items-center">
                  <div
                    className={`h-px w-8 ${node.status === "completed" ? "bg-green-500/50" : "bg-zinc-700"} `}
                  ></div>
                  <div
                    className={`ml-1 h-0 w-0 border-y-2 border-l-4 border-y-transparent ${node.status === "completed" ? "border-l-green-500/50" : "border-l-zinc-700"} `}
                  ></div>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

export default function GoalsStepsContent() {
  const [activeStep, setActiveStep] = useState(1);

  const steps = [
    {
      stepNumber: 1,
      title: "Enter or create a goal",
      helper: "Type your goal or pick from templates",
      icon: <Target02Icon className="h-3 w-3" />,
    },
    {
      stepNumber: 2,
      title: "Flowchart auto-generated",
      helper: "AI creates your step-by-step plan",
      icon: <FlowchartIcon className="h-3 w-3" />,
    },
    {
      stepNumber: 3,
      title: "Track each step",
      helper: "Monitor progress and stay motivated",
      icon: <CheckmarkCircle02Icon className="h-3 w-3" />,
    },
  ];

  const renderCanvas = () => {
    switch (activeStep) {
      case 1:
        return <EmptyStateCanvas />;
      case 2:
        return <FlowchartCanvas />;
      case 3:
        return <TrackerCanvas />;
      default:
        return <EmptyStateCanvas />;
    }
  };

  return (
    <div className="mx-auto w-full max-w-6xl">
      {/* Step Cards Row */}
      <div className="mt-16 mb-6">
        <div className="flex items-center space-x-8">
          {steps.map((step) => (
            <StepCard
              key={step.stepNumber}
              stepNumber={step.stepNumber}
              title={step.title}
              helper={step.helper}
              icon={step.icon}
              isActive={activeStep === step.stepNumber}
              onClick={() => setActiveStep(step.stepNumber)}
            />
          ))}
        </div>
      </div>

      {/* Content Canvas */}
      <div className="h-96 rounded-xl border border-zinc-800 bg-zinc-100/5">
        {renderCanvas()}
      </div>
    </div>
  );
}
