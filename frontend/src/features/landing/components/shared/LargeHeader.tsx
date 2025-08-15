import { Chip } from "@heroui/chip";

export default function LargeHeader({
  chipText,
  headingText,
  subHeadingText,
  chipText2,
}: {
  chipText?: string;
  chipText2?: string;
  headingText: string;
  subHeadingText?: string;
}) {
  return (
    <div className="flex max-w-(--breakpoint-lg) flex-col items-start text-left">
      <div className="flex w-full items-start justify-start gap-1">
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
      <h2 className="relative z-2 mt-4 mb-3 flex items-start justify-start gap-4 text-4xl font-semibold sm:text-5xl">
        {headingText}
      </h2>
      {!!subHeadingText && (
        <div className={`max-w-(--breakpoint-md) text-lg text-foreground-400`}>
          {subHeadingText}
        </div>
      )}
    </div>
  );
}
