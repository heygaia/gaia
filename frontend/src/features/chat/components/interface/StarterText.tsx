import Image from "next/image";
import { useEffect, useMemo, useState } from "react";

import { useUser } from "@/features/auth/hooks/useUser";
import { getCompleteTimeBasedGreeting } from "@/utils/greetingUtils";

// Custom hook for hourly updates
const useHourlyUpdate = () => {
  const [hour, setHour] = useState(() =>
    Math.floor(Date.now() / (1000 * 60 * 60)),
  );

  useEffect(() => {
    const updateHour = () => setHour(Math.floor(Date.now() / (1000 * 60 * 60)));

    // Calculate time until next hour
    const now = new Date();
    const nextHour = new Date(now);
    nextHour.setHours(now.getHours() + 1, 0, 0, 0);
    const timeUntilNextHour = nextHour.getTime() - now.getTime();

    // Set timeout for next hour, then interval for subsequent hours
    const timeoutId = setTimeout(() => {
      updateHour();
      const intervalId = setInterval(updateHour, 60 * 60 * 1000);
      return () => clearInterval(intervalId);
    }, timeUntilNextHour);

    return () => clearTimeout(timeoutId);
  }, []);

  return hour;
};

export default function StarterText() {
  const user = useUser();
  const hour = useHourlyUpdate();

  const greeting = useMemo(() => {
    return getCompleteTimeBasedGreeting(user?.name);
  }, [user?.name, hour]);

  return (
    <>
      <div className="my-4 inline-flex flex-wrap items-center justify-center text-center font-medium sm:gap-2">
        <div className="flex flex-col items-center gap-3">
          <div className="flex items-center gap-5 text-5xl">
            <Image
              alt="GAIA Logo"
              src="/branding/logo.webp"
              width={45}
              height={45}
            />
            <span
              suppressHydrationWarning
              className="transition-opacity duration-300"
            >
              {greeting}
            </span>
          </div>
        </div>
      </div>
    </>
  );
}
