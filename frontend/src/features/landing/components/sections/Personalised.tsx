import { BentoItem } from "./TodosBentoContent";

export default function Personalised() {
  return (
    <div className="flex flex-col items-center justify-center gap-10">
      <div className="flex w-full max-w-7xl flex-col justify-center p-7">
        <div className="mb-2 text-2xl font-light text-primary">
          Truly Personalised
        </div>
        <div className="text-5xl font-normal">
          Finally, AI that feels like it’s made for you
        </div>
        <div className="grid w-full grid-cols-3 grid-rows-1 justify-between gap-7 py-10">
          <BentoItem
            title="Receall Everything Instantly"
            description="GAIA remembers every detail you mention in a conversation"
          />
          <BentoItem
            title="Proactive Intelligence"
            description="Uses its knowledge about you to act on your behalf"
          />
          <BentoItem
            title="Build a Knowledge Graph"
            description="Builds intelligent bridges between your scattered memories"
          />
        </div>
      </div>
    </div>
  );
}
