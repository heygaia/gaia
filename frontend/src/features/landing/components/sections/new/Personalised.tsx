function BentoItem() {
  return (
    <>
      <div className="flex aspect-square flex-col gap-3">
        <div className="h-[90%] w-full min-w-full rounded-3xl bg-zinc-800" />
        <div className="flex flex-col text-xl font-light text-foreground-400">
          <span className="text-foreground">Recall Everything Instantly</span>
          Lorem ipsum dolor sit amet consectetur adipisicing elit. Repudiandae,
          soluta.
        </div>
      </div>
    </>
  );
}

export default function Personalised() {
  return (
    <div className="flex h-screen flex-col items-center justify-center gap-10">
      <div className="flex w-full max-w-7xl flex-col justify-center p-7">
        <div className="mb-2 text-2xl font-light text-primary">
          Truly Personal
        </div>
        <div className="text-5xl font-normal">
          Finally, AI that feels like it’s made for you
        </div>
        <div className="grid w-full grid-cols-3 grid-rows-1 justify-between gap-7 py-10">
          <BentoItem />
          <BentoItem />
          <BentoItem />
        </div>
      </div>
    </div>
  );
}
