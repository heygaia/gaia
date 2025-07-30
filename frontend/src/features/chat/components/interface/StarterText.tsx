import { useEffect, useState } from "react";

import { useUser } from "@/features/auth/hooks/useUser";
import { getCompleteTimeBasedGreeting } from "@/utils/greetingUtils";

// import {
//   BlushBrush02Icon,
//   Calendar01Icon,
//   DocumentAttachmentIcon,
//   FlowchartIcon,
//   GlobalSearchIcon,
//   Mic01Icon,
//   Route02Icon,
//   StickyNote01Icon,
// } from "../shared/icons";

// const badges = [
//   {
//     variant: "secondary",
//     bgClass: "bg-purple-500 hover:bg-purple-500",
//     textClass: "text-purple-500",
//     icon: (
//       <FlowchartIcon
//         className="text-purple-500 transition-colors group-hover:text-white"
//         width={17}
//       />
//     ),
//     text: "Generate Flowcharts",
//   },
//   {
//     variant: "secondary",
//     bgClass: "bg-emerald-500 hover:bg-emerald-500",
//     textClass: "text-emerald-500",
//     icon: (
//       <BlushBrush02Icon
//         className="text-emerald-500 transition-colors group-hover:text-white"
//         width={17}
//       />
//     ),
//     text: "Generate Image",
//   },
//   {
//     variant: "secondary",
//     bgClass: "bg-orange-500 hover:bg-orange-500",
//     textClass: "text-orange-500",
//     icon: (
//       <Mic01Icon
//         className="text-orange-500 transition-colors group-hover:text-white"
//         width={17}
//       />
//     ),
//     text: "Voice Conversation",
//   },
//   {
//     variant: "secondary",
//     bgClass: "bg-blue-500 hover:bg-blue-500",
//     textClass: "text-blue-500",
//     icon: (
//       <GlobalSearchIcon
//         className="text-blue-500 transition-colors group-hover:text-white"
//         width={17}
//       />
//     ),
//     text: "Internet search",
//   },
//   {
//     variant: "secondary",
//     bgClass: "bg-lime-500 hover:bg-lime-500",
//     textClass: "text-lime-500",
//     icon: (
//       <ArrowUpRight
//         className="text-lime-500 transition-colors group-hover:text-white"
//         width={17}
//       />
//     ),
//     text: "Fetch Webpage",
//   },
//   {
//     variant: "secondary",
//     bgClass: "bg-red-500 hover:bg-red-500",
//     textClass: "text-red-500",
//     icon: (
//       <Calendar01Icon
//         className="text-red-500 transition-colors group-hover:text-white"
//         width={17}
//       />
//     ),
//     text: "Manage calendar",
//   },
//   {
//     variant: "secondary",
//     bgClass: "bg-cyan-500 hover:bg-cyan-500",
//     textClass: "text-cyan-500",
//     icon: (
//       <StickyNote01Icon
//         className="text-cyan-500 transition-colors group-hover:text-white"
//         width={17}
//       />
//     ),
//     text: "Store Memories",
//   },
//   {
//     variant: "secondary",
//     bgClass: "bg-pink-500 hover:bg-pink-500",
//     textClass: "text-pink-500",
//     icon: (
//       <Route02Icon
//         className="text-pink-500 transition-colors group-hover:text-white"
//         width={17}
//       />
//     ),
//     text: "Manage goals",
//   },
//   {
//     variant: "secondary",
//     bgClass: "bg-yellow-500 hover:bg-yellow-500",
//     textClass: "text-yellow-500",
//     icon: (
//       <DocumentAttachmentIcon
//         className="text-yellow-500 transition-colors group-hover:text-white"
//         width={17}
//       />
//     ),
//     text: "chat with documents",
//   },
// ];

export default function StarterText() {
  const user = useUser();
  const [greetingData, setGreetingData] = useState(
    getCompleteTimeBasedGreeting(user?.name),
  );

  // Update greeting when user name changes and every hour to keep it current
  useEffect(() => {
    // Update greeting immediately
    setGreetingData(getCompleteTimeBasedGreeting(user?.name));

    // Set up interval to update every hour
    const interval = setInterval(() => {
      setGreetingData(getCompleteTimeBasedGreeting(user?.name));
    }, 3_600_000); // update every hour

    return () => clearInterval(interval);
  }, [user?.name]);

  return (
    <>
      <div className="my-4 inline-flex flex-wrap items-center justify-center text-center font-medium sm:gap-2">
        <div className="flex flex-col items-center gap-2">
          <div className="flex items-center gap-2 text-4xl">
            {greetingData.greeting}!
            <span className="text-2xl">{greetingData.emoji}</span>
          </div>
          {/* <div className="text-2xl">
            I'm GAIA, your personal AI assistant!
            <Image
              alt="Waving Hand"
              className="mx-2 inline w-[35px] object-contain sm:mx-2 sm:w-[40px]"
              src="https://em-content.zobj.net/source/apple/391/waving-hand_1f44b.png"
              height={30}
              width={30}
              unoptimized
            />
          </div> */}
          <div className="text-xl font-light text-gray-600 dark:text-gray-400">
            {greetingData.context} How can I help you today?
          </div>
        </div>
      </div>
      {/* <div className="flex max-w-[650px] flex-wrap justify-center gap-2">
        {badges.map((badge, index) => (
          <div
            key={index}
            className={`${badge.bgClass} bg-opacity-20 text-sm hover:bg-opacity-80 ${badge.textClass} group rounded-full px-2 font-medium transition-all hover:text-white`}
          >
            <div className="flex items-center gap-1">
              {badge.icon}
              {badge.text}
            </div>
          </div>
        ))}
      </div> */}
    </>
  );
}
