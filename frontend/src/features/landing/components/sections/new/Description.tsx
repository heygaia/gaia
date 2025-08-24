import gsap from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import { SplitText } from "gsap/SplitText";
import { useEffect, useMemo, useRef, useState } from "react";

import { OnboardingBackground } from "@/features/onboarding/components/OnboardingBackground";

import GetStartedButton from "../../shared/GetStartedButton";

export default function Description() {
  const textRefs = useRef<(HTMLDivElement | null)[]>([]);
  const containerRef = useRef<HTMLDivElement>(null);
  const sectionRef = useRef<HTMLDivElement>(null);
  const buttonRef = useRef<HTMLDivElement>(null);
  const [isSectionVisible, setIsSectionVisible] = useState(false);
  const splitTextsRef = useRef<(SplitText | null)[]>([]);

  const paragraphs = useMemo(
    () => [
      "Everyone deserves a real personal assistant — not just a chatbot.",
      "Frustrated with Siri, Alexa, or ChatGPT doing the bare minimum?",
      "Imagine an assistant that manages your digital life like a human would.",
      "Meet GAIA. Smarter. Proactive. Human-like.",
      "Because productivity should feel effortless.",
    ],
    [],
  );

  useEffect(() => {
    gsap.registerPlugin(ScrollTrigger, SplitText);

    if (
      textRefs.current.filter(Boolean).length === 0 ||
      !containerRef.current ||
      !sectionRef.current ||
      !buttonRef.current
    )
      return;

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          setIsSectionVisible(entry.isIntersecting);
        });
      },
      { threshold: 0.1 },
    );

    if (sectionRef.current) {
      observer.observe(sectionRef.current);
    }

    ScrollTrigger.getAll().forEach((st) => st.kill());
    splitTextsRef.current.forEach((st) => st?.revert());
    splitTextsRef.current = [];

    const newSplitTexts = textRefs.current.map((textRef) => {
      if (!textRef) return null;
      return new SplitText(textRef, { type: "words" });
    });
    splitTextsRef.current = newSplitTexts;

    const totalHeight = sectionRef.current.offsetHeight;
    const sectionHeight = totalHeight / paragraphs.length;

    textRefs.current.forEach((textRef) => {
      if (!textRef) return;
      gsap.set(textRef, {
        opacity: 0,
        filter: "blur(8px)",
        position: "fixed",
        top: "47%",
        left: "50%",
        transform: "translate(-50%, -50%)",
        zIndex: 10,
        visibility: "hidden",
      });
    });

    gsap.set(buttonRef.current, {
      opacity: 0,
      y: 30,
      scale: 0.9,
      visibility: "hidden",
      pointerEvents: "none",
    });

    textRefs.current.forEach((textRef, index) => {
      if (!textRef) return;

      const tl = gsap.timeline({
        scrollTrigger: {
          trigger: sectionRef.current,
          start: `top+=${index * sectionHeight} center`,
          end: `top+=${(index + 1) * sectionHeight} center`,
          scrub: 1,
          markers: false,
          onEnter: () => {
            textRefs.current.forEach((ref, i) => {
              if (ref) {
                if (i === index) {
                  gsap.set(ref, { visibility: "visible" });
                } else {
                  gsap.set(ref, {
                    visibility: "hidden",
                    opacity: 0,
                    filter: "blur(20px)",
                  });
                }
              }
            });
          },
          onEnterBack: () => {
            textRefs.current.forEach((ref, i) => {
              if (ref) {
                if (i === index) {
                  gsap.set(ref, { visibility: "visible" });
                } else {
                  gsap.set(ref, {
                    visibility: "hidden",
                    opacity: 0,
                    filter: "blur(20px)",
                  });
                }
              }
            });
          },
          onLeave: () => {
            if (textRef) {
              gsap.set(textRef, { visibility: "hidden" });
            }
          },
          onLeaveBack: () => {
            if (textRef) {
              gsap.set(textRef, { visibility: "hidden" });
            }
          },
        },
      });

      tl.to(
        textRef,
        {
          opacity: 1,
          filter: "blur(0px)",
          duration: 1,
          ease: "power2.out",
          immediateRender: false,
        },
        0,
      );

      if (newSplitTexts[index] && newSplitTexts[index]?.words) {
        tl.fromTo(
          newSplitTexts[index]!.words,
          {
            opacity: 0,
            y: 20,
            filter: "blur(5px)",
          },
          {
            opacity: 1,
            y: 0,
            filter: "blur(0px)",
            duration: 0.8,
            stagger: 0.05,
            ease: "power2.out",
          },
          0.2,
        );
      }
    });

    // Separate ScrollTrigger for button with proper boundaries
    ScrollTrigger.create({
      trigger: sectionRef.current,
      start: `top+=${(paragraphs.length - 1) * sectionHeight + sectionHeight * 0.5} center`,
      end: `bottom-=${sectionHeight * 0.2} center`,
      scrub: 1,
      onEnter: () => {
        if (buttonRef.current) {
          gsap.killTweensOf(buttonRef.current);
          gsap.set(buttonRef.current, {
            visibility: "visible",
            pointerEvents: "auto",
          });
          gsap.to(buttonRef.current, {
            opacity: 1,
            y: 0,
            scale: 1,
            duration: 0.6,
            ease: "back.out(1.7)",
            overwrite: true,
          });
        }
      },
      onLeave: () => {
        if (buttonRef.current) {
          gsap.killTweensOf(buttonRef.current);
          gsap.set(buttonRef.current, {
            visibility: "hidden",
            pointerEvents: "none",
            opacity: 0,
            y: 30,
            scale: 0.9,
          });
        }
      },
      onEnterBack: () => {
        if (buttonRef.current) {
          gsap.killTweensOf(buttonRef.current);
          gsap.set(buttonRef.current, {
            visibility: "visible",
            pointerEvents: "auto",
          });
          gsap.to(buttonRef.current, {
            opacity: 1,
            y: 0,
            scale: 1,
            duration: 0.6,
            ease: "back.out(1.7)",
            overwrite: true,
          });
        }
      },
      onLeaveBack: () => {
        if (buttonRef.current) {
          gsap.killTweensOf(buttonRef.current);
          gsap.set(buttonRef.current, {
            visibility: "hidden",
            pointerEvents: "none",
            opacity: 0,
            y: 30,
            scale: 0.9,
          });
        }
      },
    });

    return () => {
      ScrollTrigger.getAll().forEach((st) => st.kill());
      splitTextsRef.current.forEach((st) => st?.revert());
      splitTextsRef.current = [];
      observer.disconnect();
    };
  }, [paragraphs]);

  return (
    <div
      ref={sectionRef}
      className="relative mb-60 flex flex-col items-center justify-center p-20"
      style={{
        height: `${paragraphs.length * 100}vh`,
        position: "relative",
        overflow: "hidden",
      }}
    >
      <div
        className={`pointer-events-none fixed inset-0 z-[-1] h-screen w-full transition-opacity duration-700 ${
          isSectionVisible ? "opacity-100" : "opacity-0"
        }`}
      >
        <OnboardingBackground />
      </div>

      <div
        ref={containerRef}
        className="pointer-events-none relative z-10 w-full max-w-4xl"
      >
        {paragraphs.map((text, index) => (
          <div
            key={index}
            ref={(el) => {
              textRefs.current[index] = el;
            }}
            className="max-w-3xl text-center text-6xl font-medium"
            style={{ width: "100%" }}
          >
            {text}
          </div>
        ))}

        <div
          ref={buttonRef}
          className="pointer-events-auto fixed left-1/2 z-20 -translate-x-1/2 transform"
          style={{
            top: "calc(50% + 3rem)",
          }}
        >
          <GetStartedButton text="Sign Up" />
        </div>
      </div>
    </div>
  );
}
