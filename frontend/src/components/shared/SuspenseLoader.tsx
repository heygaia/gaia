import Image from "next/image";

export default function SuspenseLoader({
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
      <Image
        alt="GAIA Logo"
        src={"/images/logos/logo.webp"}
        width={30}
        height={30}
        className={`animate-spin`}
      />
    </div>
  );
}
