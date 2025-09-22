import { ReactNode } from "react";

import {
  BubbleConversationChatIcon,
  InternetIcon,
  Mail01Icon,
  Target02Icon,
} from "@/components/shared/icons";
import { Safari } from "@/components/ui/shadcn/safari";

import { MotionContainer } from "../../../../layouts/MotionContainer";

const featureOptions: { name: string; imageSrc: string; icon: ReactNode }[] = [
  {
    name: "Chat",
    imageSrc: "/landing/hero2.webp",
    icon: (
      <BubbleConversationChatIcon
        className="h-5 w-5 focus:outline-hidden"
        color={undefined}
      />
    ),
  },
  {
    name: "Goals",
    imageSrc: "/landing/goal_tracking.webp",
    icon: (
      <Target02Icon
        className="h-5 w-5 focus:outline-hidden"
        color={undefined}
      />
    ),
  },
  // {
  //   name: "calendar",
  //   imageSrc: "/landing/blur_goals.webp",
  //   icon: (
  //     <Calendar01Icon
  //       className="h-5 w-5 focus:outline-hidden"
  //       color={undefined}
  //     />
  //   ),
  // },
  {
    name: "Mail",
    imageSrc: "/landing/mail/email1.webp",
    icon: (
      <Mail01Icon className="h-5 w-5 focus:outline-hidden" color={undefined} />
    ),
  },
  {
    name: "Internet",
    imageSrc: "/landing/screenshot_internet.webp",
    icon: (
      <InternetIcon
        className="h-5 w-5 focus:outline-hidden"
        color={undefined}
      />
    ),
  },
];

export default function HeroImage() {
  // const [selectedFeature, setSelectedFeature] = useState(featureOptions[0]);
  // const [isTransitioning, setIsTransitioning] = useState(false);

  // const handleFeatureChange = (feature: {
  //   name: string;
  //   imageSrc: string;
  //   icon: ReactNode;
  // }) => {
  //   if (feature.name === selectedFeature.name) return;

  //   setIsTransitioning(true);
  //   setSelectedFeature(feature);
  //   setIsTransitioning(false);
  // };

  return (
    <div className="flex w-screen items-center justify-center">
      <MotionContainer className="mb-[20vh] flex h-fit w-screen max-w-(--breakpoint-lg) flex-col items-center justify-center gap-6 sm:mb-0 lg:max-w-(--breakpoint-xl)">
        <div className="relative scale-[175%] sm:scale-100">
          {/* <ShineBorder
            borderRadius={10}
            borderWidth={3}
            className="relative size-full w-fit min-w-fit! animate-pulse-shadow rounded-xl bg-zinc-800 p-0"
            color={["#00bbff", "#27272a"]}
            duration={7}
          > */}
          {/* ${isTransitioning ? "opacity-0" : "opacity-100"} */}
          <div className={`transition-opacity duration-300`}>
            <Safari
              className="h-fit w-full"
              imageSrc={featureOptions[0].imageSrc}
              mode="simple"
              url="heygaia.io"
            />
          </div>
          {/* {selectedFeature.name === "chat" && (
              <div className="absolute bottom-[-15px] left-0 flex w-full scale-50 items-center justify-center text-white sm:bottom-4 sm:scale-100">
                <DummySearchbar />
              </div>
            )} */}
          {/* </ShineBorder> */}

          {/* <div className="max-w-(--breakpoint-xl) w-screen bg-linear-to-b from-[#00bbff30] animate-pulse-shadow to-black bg-zinc-950 outline outline-zinc-700 min-h-[90vh] rounded-2xl z-20 flex justify-center p-10">
            <div className="flex flex-col max-w-(--breakpoint-md) w-full gap-2">
              <SimpleChatBubbleUser>
                I have a meeting this weekend could you add it to my calendar?
              </SimpleChatBubbleUser>
              <CalendarBotMessage dummyAddToCalendar={() => {}} />
              <SimpleChatBubbleUser>
                Generate Image: Golden Retriever
              </SimpleChatBubbleUser>
              <SimpleChatBubbleBot parentClassName="max-w-[300px]!">
                <GeneratedImageChatBubble
                  selectedOption={{
                    title: "Golden Retriever",
                    prompt: "cute, golden retriever",
                    src: "/generated/golden_retriever.webp",
                  }}
                />
              </SimpleChatBubbleBot>
            </div>
          </div> */}

          {/* <div className="sm:flex hidden absolute -left-28 top-0 h-full items-start animate-bounce3 ">
            <div className="bg-zinc-800 w-[250px] h-fit px-2 pb-2 rounded-3xl top-24 relative outline outline-2 outline-zinc-700 -rotate-2">
              <GeneratedImageChatBubble
                selectedOption={{
                  title: "Golden Retriever",
                  prompt: "cute, golden retriever",
                  src: "/generated/golden_retriever.webp",
                }}
              />
            </div>
          </div>

          <div className="sm:flex hidden absolute -right-28 top-0 h-full items-end">
            <div className="bg-zinc-800 w-[250px] h-[250px] rounded-xl bottom-24 relative outline outline-2 outline-zinc-700 flex items-center justify-center">
              <div className="pingspinner min-h-[100px]! min-w-[100px]!" />
            </div>
          </div> */}
        </div>
        {/* <div className="flex flex-wrap justify-center gap-2">
          {featureOptions.map((feature) => (
            <Button
              key={feature.name}
              radius="md"
              variant={selectedFeature.name === feature.name ? "solid" : "flat"}
              className={
                selectedFeature.name === feature.name ? "" : "text-primary"
              }
              color="primary"
              onPress={() => handleFeatureChange(feature)}
              startContent={feature.icon}
            >
              {feature.name}
            </Button>
          ))}
        </div> */}
      </MotionContainer>
    </div>
  );
}
