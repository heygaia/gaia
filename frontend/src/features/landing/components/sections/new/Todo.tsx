import {
  BarChart3,
  Bot,
  Calendar,
  CheckCircle,
  FolderOpen,
  ListTodo,
  MousePointer,
  Search,
  Tag,
  Target,
  User,
  Zap,
} from "lucide-react";
import React, { useEffect, useState } from "react";

import SectionChip from "../../shared/SectionChip";

interface TodoTool {
  title: string;
  description: string;
  icon: React.ReactNode;
}

const todoTools: TodoTool[] = [
  {
    title: "Smart Task Creation",
    description: "Add tasks and subtasks using natural language",
    icon: <Zap className="h-4 w-4" />,
  },
  {
    title: "Organize & Prioritize",
    description: "Sort tasks by projects, labels, due dates, or priority",
    icon: <FolderOpen className="h-4 w-4" />,
  },
  {
    title: "Quick Updates",
    description: "Edit, move, or delete tasks with simple commands",
    icon: <MousePointer className="h-4 w-4" />,
  },
  {
    title: "Powerful Search",
    description: "Find tasks using keywords or semantic search",
    icon: <Search className="h-4 w-4" />,
  },
  {
    title: "Bulk Actions",
    description: "Complete, move, or delete multiple tasks at once",
    icon: <CheckCircle className="h-4 w-4" />,
  },
  {
    title: "Project Management",
    description: "Group tasks under color-coded projects",
    icon: <FolderOpen className="h-4 w-4" />,
  },
  {
    title: "Subtasks",
    description: "Break big tasks into smaller steps",
    icon: <ListTodo className="h-4 w-4" />,
  },
  {
    title: "Labels & Tags",
    description: "Categorize tasks with custom labels",
    icon: <Tag className="h-4 w-4" />,
  },
  {
    title: "Task Statistics",
    description: "View progress and productivity stats",
    icon: <BarChart3 className="h-4 w-4" />,
  },
  {
    title: "Priority Levels",
    description: "Focus using task priority settings",
    icon: <Target className="h-4 w-4" />,
  },
  {
    title: "Due Dates",
    description: "Set and track task deadlines",
    icon: <Calendar className="h-4 w-4" />,
  },
  {
    title: "Smart Notifications",
    description: "Get reminded at the perfect time",
    icon: <Zap className="h-4 w-4" />,
  },
];

const FeatureCard: React.FC<{
  children: React.ReactNode;
  className?: string;
}> = ({ children, className = "" }) => (
  <div
    className={`relative overflow-hidden rounded-2xl border border-white/10 bg-gradient-to-br from-white/5 to-white/[0.02] shadow-lg backdrop-blur-sm transition-all duration-200 hover:border-[#01BBFF]/20 hover:shadow-xl hover:shadow-[#01BBFF]/5 ${className} `}
  >
    {children}
  </div>
);

const ChatAnimation: React.FC = () => {
  const [currentStep, setCurrentStep] = useState(0);
  const [showCheckmark, setShowCheckmark] = useState(false);

  const messages = [
    {
      type: "user",
      text: "Create a task to review quarterly reports by Friday",
    },
    { type: "ai", text: "Task created successfully!" },
  ];

  const tasks = [
    {
      id: 1,
      text: "Review quarterly reports",
      priority: "high",
      completed: false,
    },
    {
      id: 2,
      text: "Schedule team meeting",
      priority: "medium",
      completed: true,
    },
    {
      id: 3,
      text: "Update project documentation",
      priority: "low",
      completed: false,
    },
  ];

  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentStep((prev) => {
        if (prev === 0) {
          setTimeout(() => setCurrentStep(1), 1500);
          return 0;
        } else if (prev === 1) {
          setTimeout(() => {
            setShowCheckmark(true);
            setTimeout(() => {
              setShowCheckmark(false);
              setCurrentStep(0);
            }, 2000);
          }, 1000);
          return 1;
        }
        return 0;
      });
    }, 5000);

    return () => clearInterval(timer);
  }, []);

  return (
    <div className="space-y-6">
      {/* Chat Interface */}
      <div className="rounded-xl border border-white/5 bg-slate-800/30 p-4">
        <div className="space-y-3">
          {/* User Message */}
          <div
            className={`flex items-start justify-end gap-3 transition-all duration-500 ${currentStep >= 0 ? "translate-y-0 opacity-100" : "translate-y-4 opacity-0"}`}
          >
            <div className="max-w-xs rounded-2xl bg-slate-800/50 px-4 py-2">
              <p className="text-sm text-white">{messages[0].text}</p>
            </div>
            <div className="flex h-8 w-8 items-center justify-center rounded-full bg-slate-700">
              <User className="h-4 w-4 text-white" />
            </div>
          </div>

          {/* AI Response */}
          <div
            className={`flex items-start justify-start gap-3 transition-all delay-1000 duration-500 ${currentStep >= 1 ? "translate-y-0 opacity-100" : "translate-y-4 opacity-0"}`}
          >
            <div className="flex h-8 w-8 items-center justify-center rounded-full bg-gradient-to-br from-[#01BBFF] to-cyan-400">
              <Bot className="h-4 w-4 text-white" />
            </div>
            <div className="max-w-xs rounded-2xl border border-[#01BBFF]/30 bg-[#01BBFF]/20 px-4 py-2">
              <p className="flex items-center gap-2 text-sm text-[#01BBFF]">
                <CheckCircle className="h-4 w-4" />
                {messages[1].text}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Task List */}
      <div className="rounded-xl border border-white/5 bg-slate-800/30 p-4">
        <div className="space-y-2">
          {tasks.map((task, index) => (
            <div
              key={task.id}
              className={`flex items-center gap-3 rounded-lg bg-slate-800/30 p-3 transition-all duration-300 ${
                index === 0 && showCheckmark
                  ? "border border-[#01BBFF]/30 bg-[#01BBFF]/10"
                  : ""
              }`}
            >
              <div
                className={`flex h-5 w-5 items-center justify-center rounded-full border-2 transition-all duration-300 ${
                  task.completed || (index === 0 && showCheckmark)
                    ? "border-[#01BBFF] bg-[#01BBFF]"
                    : "border-slate-500"
                }`}
              >
                {(task.completed || (index === 0 && showCheckmark)) && (
                  <CheckCircle className="h-3 w-3 text-white" />
                )}
              </div>
              <span
                className={`flex-1 text-sm transition-all duration-300 ${
                  task.completed ? "text-slate-400 line-through" : "text-white"
                }`}
              >
                {task.text}
              </span>
              <span
                className={`rounded-full px-2 py-1 text-xs ${
                  task.priority === "high"
                    ? "bg-red-500/20 text-red-400"
                    : task.priority === "medium"
                      ? "bg-yellow-500/20 text-yellow-400"
                      : "bg-green-500/20 text-green-400"
                }`}
              >
                {task.priority}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default function Todo() {
  return (
    <div className="relative min-h-screen overflow-hidden">
      <div className="bg relative z-10 container mx-auto max-w-7xl py-20">
        {/* Header Section */}
        <div className="mb-16 text-center">
          <SectionChip icon={CheckCircle} text="To-do lists" />

          <div className="relative mb-3">
            <h1 className="relative z-10 bg-gradient-to-r from-white via-white to-gray-400 bg-clip-text text-4xl leading-tight font-bold text-transparent md:text-5xl lg:text-6xl">
              Save Hours on&nbsp;
              <span>Task Management</span>
            </h1>
          </div>

          <p className="mx-auto max-w-2xl text-xl leading-relaxed text-gray-400 md:text-2xl">
            Stop wasting time organizing your to-dos — GAIA manages everything
            for you through simple text.
          </p>
        </div>

        {/* Bento Grid */}
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 md:gap-6 lg:grid-cols-4">
          {/* Chat Management Card */}
          <FeatureCard className="md:col-span-2 lg:col-span-2 lg:row-span-2">
            <div className="flex h-full min-h-[400px] flex-col p-6 md:p-8 lg:min-h-[500px]">
              <div className="mb-6">
                <h3 className="mb-2 text-xl font-bold text-white md:text-2xl">
                  Easily Manage Tasks Through Chat
                </h3>
                <p className="text-sm text-gray-400 md:text-base">
                  Type messages to create and manage your tasks
                </p>
              </div>
              <div className="flex-1">
                <ChatAnimation />
              </div>
            </div>
          </FeatureCard>

          {/* Tools List Card */}
          <FeatureCard className="md:col-span-2 lg:col-span-2 lg:row-span-2">
            <div className="h-full min-h-[400px] p-6 md:p-8 lg:min-h-[500px]">
              <div className="mb-6">
                <h3 className="mb-2 text-xl font-bold text-white md:text-2xl">
                  {todoTools.length}+ Todo Tools
                </h3>
                <p className="text-sm text-gray-400 md:text-base">
                  Stop wasting time organizing to-do lists — GAIA turns your
                  words into action instantly
                </p>
              </div>
              <div className="custom-scrollbar grid max-h-80 grid-cols-1 gap-3 overflow-y-auto sm:grid-cols-2">
                {todoTools.map((tool, index) => (
                  <div key={index} className="group/item">
                    <div className="h-full rounded-xl border border-white/5 bg-slate-800/30 p-4 backdrop-blur-sm transition-all duration-300 hover:border-[#01BBFF]/20 hover:bg-slate-800/50">
                      <div className="flex items-start gap-3">
                        <div className="mt-1 text-[#01BBFF] opacity-70 transition-opacity group-hover/item:opacity-100">
                          {tool.icon}
                        </div>
                        <div className="flex-1">
                          <h4 className="mb-1 text-sm font-semibold text-white">
                            {tool.title}
                          </h4>
                          <p className="text-xs leading-relaxed text-gray-400">
                            {tool.description}
                          </p>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </FeatureCard>

          {/* Easy Task Creation */}
          <FeatureCard className="md:col-span-2 lg:col-span-2">
            <div className="h-full min-h-[200px] p-6 md:p-8">
              <div className="mb-6">
                <h3 className="mb-2 text-xl font-bold text-white md:text-2xl">
                  Easy Task Creation
                </h3>
                <p className="text-sm text-gray-400 md:text-base">
                  Create tasks using everyday language
                </p>
              </div>
              <div className="rounded-xl border border-white/5 bg-slate-800/30 p-4 md:p-6">
                <div className="space-y-3">
                  <div className="flex items-center gap-3">
                    <div className="h-2 w-2 rounded-full bg-[#01BBFF]" />
                    <span className="text-sm text-white">
                      "Add meeting with John tomorrow at 2pm"
                    </span>
                  </div>
                  <div className="flex items-center gap-3">
                    <div className="h-2 w-2 rounded-full bg-[#01BBFF]" />
                    <span className="text-sm text-white">
                      "Remind me to call mom this weekend"
                    </span>
                  </div>
                  <div className="flex items-center gap-3">
                    <div className="h-2 w-2 rounded-full bg-[#01BBFF]" />
                    <span className="text-sm text-white">
                      "Buy groceries after work"
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </FeatureCard>

          {/* View Task Details */}
          <FeatureCard className="lg:col-span-1">
            <div className="h-full min-h-[200px] p-6">
              <div className="mb-4">
                <h3 className="mb-1 text-lg font-bold text-white">
                  View Task Details
                </h3>
                <p className="text-sm text-gray-400">
                  See subtasks, descriptions, and task structure
                </p>
              </div>
              <div className="space-y-2">
                <div className="rounded-lg border border-white/5 bg-slate-800/30 p-3">
                  <div className="flex items-center gap-2">
                    <CheckCircle className="h-4 w-4 text-[#01BBFF]" />
                    <span className="text-sm text-white">
                      Research competitors
                    </span>
                  </div>
                </div>
                <div className="rounded-lg border border-white/5 bg-slate-800/30 p-3">
                  <div className="flex items-center gap-2">
                    <div className="h-4 w-4 rounded-full border-2 border-gray-400" />
                    <span className="text-sm text-white">
                      Create presentation
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </FeatureCard>

          {/* Organize Tasks */}
          <FeatureCard className="lg:col-span-1">
            <div className="h-full min-h-[200px] p-6">
              <div className="mb-4">
                <h3 className="mb-1 text-lg font-bold text-white">
                  Organize Your Tasks
                </h3>
                <p className="text-sm text-gray-400">
                  Sort tasks by priority, labels, and projects
                </p>
              </div>
              <div className="space-y-2">
                <div className="flex items-center gap-2">
                  <div className="h-3 w-3 rounded-full bg-[#01BBFF]" />
                  <span className="text-sm text-white">High Priority</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="h-3 w-3 rounded-full bg-[#01BBFF]/60" />
                  <span className="text-sm text-white">Medium Priority</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="h-3 w-3 rounded-full bg-[#01BBFF]/30" />
                  <span className="text-sm text-white">Low Priority</span>
                </div>
              </div>
            </div>
          </FeatureCard>
        </div>
      </div>

      <style jsx>{`
        .custom-scrollbar::-webkit-scrollbar {
          width: 4px;
        }
        .custom-scrollbar::-webkit-scrollbar-track {
          background: rgba(255, 255, 255, 0.1);
          border-radius: 2px;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb {
          background: #01bbff;
          border-radius: 2px;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb:hover {
          background: #0199cc;
        }
      `}</style>
    </div>
  );
}
