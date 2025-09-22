import { memo } from "react";

// Lightweight CSS-only loader to reduce JS execution time
const SuspenseLoader = memo(function SuspenseLoader({
  fullHeight = false,
  fullWidth = false,
}: {
  fullHeight?: boolean;
  fullWidth?: boolean;
}) {
  return (
    <div
      className={`w-full ${fullHeight ? "h-screen" : "h-full"} ${
        fullWidth ? "w-screen" : "w-full"
      } flex items-center justify-center p-3`}
    >
      <div
        className="h-8 w-8 animate-spin rounded-full border-2 border-zinc-600 border-t-white"
        role="status"
        aria-label="Loading content"
      />
    </div>
  );
});

export default SuspenseLoader;
