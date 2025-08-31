import { BentoItem } from "./new/TodosBentoContent";

export default function WorkflowSection() {
  return (
    <div className="flex w-full max-w-7xl flex-col justify-center p-7">
      <div className="mb-2 text-2xl font-light text-primary">
        Your Daily Life, Automated
      </div>
      <div className="mb-5 text-5xl font-normal">
        Simple workflows to eliminate repetitive tasks
      </div>

      <div className="grid w-full max-w-7xl grid-cols-3 grid-rows-1 justify-between gap-7">
        <BentoItem
          title="Smart Triggers"
          description="Set conditions once, automate actions forever."
        />
        <BentoItem
          title="Proactive by Nature"
          description="GAIA acts before you ask, preparing what you need when you need it."
        />
        <BentoItem
          title="Seamless Orchestration"
          description="Makes all your apps work together like a single tool, through a unified interface."
        />
      </div>
    </div>
  );
}
