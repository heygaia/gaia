import { AnimatePresence, motion } from "framer-motion";
import {
  Bell,
  Calendar,
  CheckCircle,
  Clock,
  GitBranch,
  List,
  Mail,
  Play,
  Plus,
  Target,
  User,
  Zap,
} from "lucide-react";
import React, { useCallback, useEffect, useState } from "react";
import { useInView } from "react-intersection-observer";

interface WorkflowStep {
  id: number;
  title: string;
  description: string;
  action: string;
  status: "pending" | "running" | "completed";
  icon: React.ReactNode;
}

interface CalendarEvent {
  id: string;
  title: string;
  date: string;
  time: string;
  type: "reminder" | "deadline";
}

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
    transition={{ duration: 0.4, ease: [0.25, 0.46, 0.45, 0.94] }}
  />
);

const SectionChip: React.FC<{ icon: React.ElementType; text: string }> = ({
  icon: Icon,
  text,
}) => (
  <motion.div
    initial={{ opacity: 0, y: 10 }}
    animate={{ opacity: 1, y: 0 }}
    transition={{ duration: 0.6, ease: [0.25, 0.46, 0.45, 0.94] }}
    className="mb-6 flex items-center justify-center"
  >
    <div className="flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-4 py-2 backdrop-blur-sm">
      <Icon className="h-4 w-4 text-[#01BBFF]" />
      <span className="text-sm font-medium text-white">{text}</span>
    </div>
  </motion.div>
);

const LargeHeader: React.FC<{
  headingText: string;
  subHeadingText: string;
}> = ({ headingText, subHeadingText }) => (
  <header className="mb-12 text-center">
    <SectionChip icon={Zap} text="AI Workflow Generator" />

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

const WorkflowAutomation: React.FC = () => {
  const { ref, inView } = useInView({
    triggerOnce: true,
    threshold: 0.4,
  });

  const [stage, setStage] = useState("input");
  const [isGenerating, setIsGenerating] = useState(false);
  const [isRunning, setIsRunning] = useState(false);
  const [currentStep, setCurrentStep] = useState(0);
  const [showCompleted, setShowCompleted] = useState(false);
  const [calendarEvents, setCalendarEvents] = useState<CalendarEvent[]>([]);
  const [highlightAssignment, setHighlightAssignment] = useState(false);
  const [, setEventsAnimated] = useState(false);

  const workflowSteps: WorkflowStep[] = [
    {
      id: 1,
      title: "Create Main Task",
      description: "Creating task in Google Tasks",
      action: "Google Tasks",
      status: "pending",
      icon: <Plus className="h-4 w-4" />,
    },
    {
      id: 2,
      title: "Break Into Subtasks",
      description: "Adding research, implementation, and documentation",
      action: "Google Tasks",
      status: "pending",
      icon: <List className="h-4 w-4" />,
    },
    {
      id: 3,
      title: "Set Deadline",
      description: "Adding project deadline for next Friday",
      action: "Google Calendar",
      status: "pending",
      icon: <Clock className="h-4 w-4" />,
    },
    {
      id: 4,
      title: "Schedule Sessions",
      description: "Creating daily work reminders",
      action: "Google Calendar",
      status: "pending",
      icon: <Bell className="h-4 w-4" />,
    },
  ];

  const [steps, setSteps] = useState(workflowSteps);

  const generateWorkflow = useCallback(async () => {
    setIsGenerating(true);
    setHighlightAssignment(true);

    await new Promise((resolve) => setTimeout(resolve, 2000));

    setStage("workflow");
    setIsGenerating(false);
    setHighlightAssignment(false);
  }, []);

  const runWorkflow = useCallback(async () => {
    setIsRunning(true);
    setStage("execution");

    for (let i = 0; i < steps.length; i++) {
      setCurrentStep(i);

      // Set current step to running
      setSteps((prev) =>
        prev.map((step, index) => ({
          ...step,
          status: index === i ? "running" : index < i ? "completed" : "pending",
        })),
      );

      await new Promise((resolve) => setTimeout(resolve, 1500));

      // Add calendar events for reminder step and animate them
      if (i === 3) {
        setCalendarEvents([
          {
            id: "1",
            title: "Research & Planning",
            date: "Dec 9",
            time: "2:00 PM",
            type: "reminder",
          },
          {
            id: "2",
            title: "Implement Algorithms",
            date: "Dec 10",
            time: "3:00 PM",
            type: "reminder",
          },
          {
            id: "3",
            title: "Testing & Documentation",
            date: "Dec 11",
            time: "4:00 PM",
            type: "reminder",
          },
          {
            id: "4",
            title: "Assignment Due",
            date: "Dec 13",
            time: "11:59 PM",
            type: "deadline",
          },
        ]);

        // Wait for calendar events to animate
        await new Promise((resolve) => setTimeout(resolve, 800));
        setEventsAnimated(true);
      }

      // Set current step to completed
      setSteps((prev) =>
        prev.map((step, index) => ({
          ...step,
          status: index <= i ? "completed" : "pending",
        })),
      );
    }

    setIsRunning(false);

    // Wait a bit more before showing completion
    await new Promise((resolve) => setTimeout(resolve, 1000));
    setShowCompleted(true);

    // Auto restart after completion
    setTimeout(() => {
      resetWorkflow();
    }, 2500);
  }, [steps.length]);

  const resetWorkflow = useCallback(() => {
    setSteps(workflowSteps);
    setCurrentStep(0);
    setIsRunning(false);
    setShowCompleted(false);
    setCalendarEvents([]);
    setEventsAnimated(false);
    setHighlightAssignment(false);
    setStage("input");
  }, []);

  // Auto-start the demo when in view and loop
  useEffect(() => {
    if (!inView) return;

    const startDemo = async () => {
      await new Promise((resolve) => setTimeout(resolve, 1000));
      await generateWorkflow();
      await new Promise((resolve) => setTimeout(resolve, 1000));
      await runWorkflow();
    };

    startDemo();
  }, [inView, generateWorkflow, runWorkflow]);

  const getStepStatusColor = (status: string) => {
    switch (status) {
      case "completed":
        return "border-[#01BBFF]/30 bg-[#01BBFF]/5";
      case "running":
        return "border-yellow-500/30 bg-yellow-500/5";
      default:
        return "border-white/10 bg-white/[0.02]";
    }
  };

  return (
    <div className="bg-grid-white/[0.05] relative min-h-screen w-full overflow-x-hidden bg-[radial-gradient(ellipse_at_top_left,_#0f0f0f,_#09090b)] bg-cover bg-fixed bg-no-repeat">
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_50%_50%,rgba(1,187,255,0.05),transparent_50%)]" />
      <div className="absolute inset-0 bg-[linear-gradient(to_right,#80808008_1px,transparent_1px),linear-gradient(to_bottom,#80808008_1px,transparent_1px)] bg-[size:32px_32px]" />

      <div className="relative z-10 container mx-auto flex min-h-screen max-w-7xl flex-col items-center justify-center gap-12 px-4 py-12 sm:py-16 md:gap-16 md:py-24">
        <LargeHeader
          headingText="Smart Assignment Automation"
          subHeadingText="Watch GAIA transform your assignment into a complete automated workflow across Google Workspace"
        />

        {/* Main Demo Container */}
        <div
          ref={ref}
          className="anim-container relative h-[650px] w-full max-w-7xl overflow-hidden rounded-3xl border border-white/10 bg-gradient-to-br from-white/[0.02] to-transparent shadow-2xl shadow-black/40 backdrop-blur-2xl"
        >
          <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_30%_40%,rgba(1,187,255,0.1),transparent_50%)]" />
          <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_70%_60%,rgba(6,182,212,0.1),transparent_50%)]" />

          <div className="flex h-full items-center justify-center p-8">
            <AnimatePresence mode="wait">
              {/* Input Stage */}
              {stage === "input" && (
                <motion.div
                  key="input"
                  initial={{ opacity: 0, scale: 0.95 }}
                  animate={{ opacity: 1, scale: 1 }}
                  exit={{ opacity: 0, scale: 0.95 }}
                  transition={{ duration: 0.6, ease: [0.25, 0.46, 0.45, 0.94] }}
                  className="w-full max-w-4xl"
                >
                  <div className="rounded-2xl border border-white/10 bg-white/[0.02] backdrop-blur-sm">
                    <div className="border-b border-white/10 p-6">
                      <div className="flex items-center gap-4">
                        <div className="flex h-10 w-10 items-center justify-center rounded-lg border border-[#01BBFF]/20 bg-[#01BBFF]/10">
                          <User className="h-5 w-5 text-[#01BBFF]" />
                        </div>
                        <div>
                          <h3 className="text-lg font-semibold text-white">
                            Assignment Input
                          </h3>
                          <p className="text-sm text-gray-400">
                            Tell GAIA about your assignment
                          </p>
                        </div>
                      </div>
                    </div>

                    <div className="p-6">
                      <div
                        className={`mb-4 rounded-lg border p-4 transition-all duration-500 ${
                          highlightAssignment
                            ? "border-[#01BBFF]/50 bg-[#01BBFF]/5"
                            : "border-white/10 bg-white/[0.02]"
                        }`}
                      >
                        <p className="text-base leading-relaxed text-white">
                          "Create a complete workflow for my Computer Science
                          assignment:
                          <span className="font-medium text-[#01BBFF]">
                            {" "}
                            Implement a sorting algorithm comparison project
                          </span>
                          - due next Friday."
                        </p>
                      </div>

                      <div className="flex items-center gap-3 rounded-lg border border-[#01BBFF]/20 bg-[#01BBFF]/5 p-3 text-sm text-[#01BBFF]">
                        <Zap className="h-4 w-4 flex-shrink-0 text-[#01BBFF]" />
                        <span className="font-medium">
                          {isGenerating
                            ? "GAIA is analyzing your assignment..."
                            : "Ready to generate workflow"}
                        </span>
                        {isGenerating && (
                          <div className="ml-auto flex space-x-1">
                            <div
                              className="h-1 w-1 animate-bounce rounded-full bg-[#01BBFF]"
                              style={{ animationDelay: "0s" }}
                            ></div>
                            <div
                              className="h-1 w-1 animate-bounce rounded-full bg-[#01BBFF]"
                              style={{ animationDelay: "0.1s" }}
                            ></div>
                            <div
                              className="h-1 w-1 animate-bounce rounded-full bg-[#01BBFF]"
                              style={{ animationDelay: "0.2s" }}
                            ></div>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                </motion.div>
              )}

              {/* Workflow & Execution Stages */}
              {(stage === "workflow" || stage === "execution") && (
                <motion.div
                  key="workflow"
                  initial={{ opacity: 0, scale: 0.95 }}
                  animate={{ opacity: 1, scale: 1 }}
                  exit={{ opacity: 0, scale: 0.95 }}
                  transition={{ duration: 0.6, ease: [0.25, 0.46, 0.45, 0.94] }}
                  className="grid h-full w-full max-w-6xl grid-cols-1 gap-6 lg:grid-cols-3"
                >
                  {/* Generated Workflow */}
                  <div className="flex flex-col lg:col-span-2">
                    <div className="flex-1 rounded-2xl border border-white/10 bg-white/[0.02] backdrop-blur-sm">
                      <div className="border-b border-white/10 p-4">
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-3">
                            <GitBranch className="h-5 w-5 text-[#01BBFF]" />
                            <h3 className="text-lg font-semibold text-white">
                              Generated Workflow
                            </h3>
                          </div>

                          {stage === "workflow" && (
                            <motion.button
                              initial={{ opacity: 0, scale: 0.9 }}
                              animate={{ opacity: 1, scale: 1 }}
                              transition={{ delay: 0.3, duration: 0.4 }}
                              onClick={runWorkflow}
                              className="flex items-center gap-2 rounded-lg bg-[#01BBFF] px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-[#01BBFF]/90"
                            >
                              <Play className="h-4 w-4" />
                              Execute
                            </motion.button>
                          )}
                        </div>
                      </div>

                      <div className="flex-1 overflow-y-auto p-4">
                        <div className="space-y-3">
                          {steps.map((step, index) => (
                            <motion.div
                              key={step.id}
                              className="relative"
                              initial={{ opacity: 0, x: -20 }}
                              animate={{ opacity: 1, x: 0 }}
                              transition={{ delay: index * 0.1, duration: 0.5 }}
                            >
                              <div
                                className={`rounded-lg border p-4 transition-all duration-500 ${getStepStatusColor(step.status)}`}
                              >
                                <div className="flex items-center gap-4">
                                  {/* Step Icon */}
                                  <div
                                    className={`flex h-8 w-8 items-center justify-center rounded-lg transition-all duration-300 ${
                                      step.status === "completed"
                                        ? "bg-[#01BBFF] text-white"
                                        : step.status === "running"
                                          ? "bg-yellow-500 text-white"
                                          : "bg-white/5 text-gray-400"
                                    }`}
                                  >
                                    {step.status === "completed" ? (
                                      <CheckCircle className="h-4 w-4" />
                                    ) : step.status === "running" ? (
                                      <motion.div
                                        className="h-3 w-3 rounded-full border-2 border-white border-t-transparent"
                                        animate={{ rotate: 360 }}
                                        transition={{
                                          duration: 1,
                                          repeat: Infinity,
                                          ease: "linear",
                                        }}
                                      />
                                    ) : (
                                      step.icon
                                    )}
                                  </div>

                                  {/* Step Content */}
                                  <div className="flex-1">
                                    <div className="mb-1 flex items-center gap-2">
                                      <h4 className="text-sm font-medium text-white">
                                        {step.title}
                                      </h4>
                                      <span
                                        className={`rounded-full px-2 py-1 text-xs ${
                                          step.status === "completed"
                                            ? "bg-[#01BBFF]/20 text-[#01BBFF]"
                                            : step.status === "running"
                                              ? "bg-yellow-500/20 text-yellow-400"
                                              : "bg-white/10 text-gray-400"
                                        }`}
                                      >
                                        {step.action}
                                      </span>
                                    </div>
                                    <p className="text-xs text-gray-400">
                                      {step.description}
                                    </p>
                                  </div>
                                </div>
                              </div>
                            </motion.div>
                          ))}
                        </div>
                      </div>
                    </div>

                    {/* Progress Bar */}
                    {isRunning && (
                      <motion.div
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        className="mt-4 rounded-lg border border-[#01BBFF]/20 bg-[#01BBFF]/5 p-3"
                      >
                        <div className="mb-2 flex items-center justify-between">
                          <span className="text-sm font-medium text-[#01BBFF]">
                            Step {currentStep + 1} of {steps.length}
                          </span>
                          <span className="text-xs text-[#01BBFF]">
                            {Math.round(
                              ((currentStep + 1) / steps.length) * 100,
                            )}
                            %
                          </span>
                        </div>
                        <div className="h-1.5 rounded-full bg-white/10">
                          <motion.div
                            className="h-1.5 rounded-full bg-[#01BBFF]"
                            initial={{ width: 0 }}
                            animate={{
                              width: `${((currentStep + 1) / steps.length) * 100}%`,
                            }}
                            transition={{ duration: 0.3 }}
                          />
                        </div>
                      </motion.div>
                    )}
                  </div>

                  {/* Google Calendar Widget */}
                  <div className="lg:col-span-1">
                    <div className="h-full rounded-2xl border border-white/10 bg-white/[0.02] backdrop-blur-sm">
                      <div className="border-b border-white/10 p-4">
                        <div className="flex items-center gap-3">
                          <GoogleLogo
                            src="https://upload.wikimedia.org/wikipedia/commons/thumb/a/a5/Google_Calendar_icon_%282020%29.svg/640px-Google_Calendar_icon_%282020%29.svg.png"
                            alt="Google Calendar"
                            className="h-5 w-5"
                          />
                          <h3 className="text-lg font-semibold text-white">
                            Google Calendar
                          </h3>
                        </div>
                      </div>

                      <div className="h-full p-4">
                        {calendarEvents.length === 0 ? (
                          <div className="flex h-full flex-col items-center justify-center text-center">
                            <Calendar className="mb-2 h-8 w-8 text-gray-400" />
                            <p className="text-sm text-gray-400">
                              Events will appear here
                            </p>
                          </div>
                        ) : (
                          <div className="space-y-3">
                            {calendarEvents.map((event, index) => (
                              <motion.div
                                key={event.id}
                                initial={{ opacity: 0, y: 20 }}
                                animate={{ opacity: 1, y: 0 }}
                                transition={{
                                  delay: index * 0.1,
                                  duration: 0.5,
                                }}
                                className={`rounded-lg border p-3 ${
                                  event.type === "deadline"
                                    ? "border-red-500/30 bg-red-500/10"
                                    : "border-[#01BBFF]/30 bg-[#01BBFF]/10"
                                }`}
                              >
                                <div className="flex items-start gap-3">
                                  <div
                                    className={`mt-1 ${
                                      event.type === "deadline"
                                        ? "text-red-400"
                                        : "text-[#01BBFF]"
                                    }`}
                                  >
                                    {event.type === "deadline" ? (
                                      <Clock className="h-4 w-4" />
                                    ) : (
                                      <Bell className="h-4 w-4" />
                                    )}
                                  </div>
                                  <div className="flex-1">
                                    <h4 className="text-sm font-medium text-white">
                                      {event.title}
                                    </h4>
                                    <p className="mt-1 text-xs text-gray-400">
                                      {event.date} • {event.time}
                                    </p>
                                  </div>
                                </div>
                              </motion.div>
                            ))}
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>

          {/* Completion Overlay */}
          <AnimatePresence>
            {showCompleted && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="absolute inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm"
              >
                <motion.div
                  initial={{ opacity: 0, scale: 0.9 }}
                  animate={{ opacity: 1, scale: 1 }}
                  exit={{ opacity: 0, scale: 0.9 }}
                  className="text-center"
                >
                  <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-green-500/20">
                    <CheckCircle className="h-8 w-8 text-green-400" />
                  </div>
                  <h3 className="mb-2 text-xl font-semibold text-white">
                    Workflow Completed!
                  </h3>
                  <p className="text-gray-300">
                    All tasks and reminders set up automatically
                  </p>
                </motion.div>
              </motion.div>
            )}
          </AnimatePresence>

          {/* Status Indicator */}
          <div className="absolute top-6 left-1/2 z-40 -translate-x-1/2 transform">
            <div className="rounded-full border border-white/20 bg-black/80 px-4 py-2 text-white backdrop-blur-lg">
              <div className="flex items-center gap-2">
                <div className="text-[#01BBFF]">
                  {stage === "input" && <Mail className="h-4 w-4" />}
                  {stage === "workflow" && <Target className="h-4 w-4" />}
                  {stage === "execution" && <Zap className="h-4 w-4" />}
                </div>
                <span className="text-sm font-medium">
                  {stage === "input" &&
                    (isGenerating
                      ? "Analyzing Assignment"
                      : "Assignment Input")}
                  {stage === "workflow" && "Workflow Generated"}
                  {stage === "execution" && "Executing Workflow"}
                </span>
                {(isGenerating || isRunning) && (
                  <div className="ml-2 flex space-x-1">
                    <div className="h-1 w-1 animate-pulse rounded-full bg-white/60"></div>
                    <div
                      className="h-1 w-1 animate-pulse rounded-full bg-white/60"
                      style={{ animationDelay: "0.2s" }}
                    ></div>
                    <div
                      className="h-1 w-1 animate-pulse rounded-full bg-white/60"
                      style={{ animationDelay: "0.4s" }}
                    ></div>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default WorkflowAutomation;
