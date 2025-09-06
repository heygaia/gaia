import { cn } from "@/lib";

export function BentoItem({
  title,
  description,
  children,
  childrenClassName,
}: {
  title: string;
  description: string;
  children?: React.ReactNode;
  childrenClassName?: string;
}) {
  return (
    <div className="flex aspect-square flex-col gap-3">
      <div
        className={cn(
          "flex h-[90%] w-full min-w-full items-center justify-center rounded-3xl bg-zinc-800/70 p-4",
          childrenClassName,
        )}
      >
        {children}
      </div>
      <div className="flex flex-col text-xl text-foreground-400">
        <span className="text-foreground">{title}</span>
        <span className="font-light">{description}</span>
      </div>
    </div>
  );
}

export default function TodosBentoContent() {
  return (
    <div>
      <div className="grid w-full grid-cols-3 grid-rows-1 justify-between gap-7 p-4">
        <BentoItem
          title="Smart Task Organization"
          description="Automatically categorize and prioritize your tasks based on deadlines and importance."
        />
        <BentoItem
          title="Natural Language Planning"
          description="Just tell GAIA what you need to do - it converts your thoughts into actionable tasks."
        />
        <BentoItem
          title="Intelligent Reminders"
          description="Get timely reminders and suggestions to help you stay on track with your goals."
        />
      </div>
    </div>
  );
}
