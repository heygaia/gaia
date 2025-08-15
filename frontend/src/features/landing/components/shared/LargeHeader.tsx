import { Chip } from "@heroui/chip";

export default function LargeHeader({
  chipText,
  headingText,
  subHeadingText,
  chipText2,
  centered = false,
}: {
  chipText?: string;
  chipText2?: string;
  headingText: string;
  subHeadingText?: string;
  centered?: boolean;
}) {
  return (
    <div
      className={`flex max-w-(--breakpoint-lg) flex-col ${centered ? "items-center text-center" : "items-start text-left"}`}
    >
      <div
        className={`flex w-full gap-1 ${centered ? "items-center justify-center" : "items-start justify-start"}`}
      >
        {chipText && (
          <Chip variant="flat" color="primary">
            {chipText}
          </Chip>
        )}

        {chipText2 && (
          <Chip variant="flat" color="danger">
            {chipText2}
          </Chip>
        )}
      </div>
      <h2
        className={`relative z-2 mt-4 mb-3 flex gap-4 text-4xl font-semibold sm:text-5xl ${centered ? "items-center justify-center" : "items-start justify-start"}`}
      >
        {headingText}
      </h2>
      {!!subHeadingText && (
        <div
          className={`max-w-(--breakpoint-md) text-lg text-foreground-400 ${centered ? "text-center" : ""}`}
        >
          {subHeadingText}
        </div>
      )}
    </div>
  );
}
