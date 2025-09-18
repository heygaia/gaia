import { AnimatePresence, motion } from "framer-motion";
import { CheckCircle2, ExternalLink, Globe, Search } from "lucide-react";
import Image from "next/image";
import React, { useEffect, useState } from "react";

// --- REUSABLE & CONSISTENT COMPONENTS (ANIMATED) ---

const SectionChip: React.FC<{ icon: React.ElementType; text: string }> = ({
  icon: Icon,
  text,
}) => (
  <div className="mb-4 inline-flex items-center justify-center gap-2 rounded-full border border-white/10 bg-white/5 px-4 py-2">
    <Icon className="h-4 w-4 text-[#01BBFF]" />
    <span className="text-sm font-medium text-gray-300">{text}</span>
  </div>
);

const FeatureCard: React.FC<{
  children: React.ReactNode;
  className?: string;
}> = ({ children, className = "" }) => (
  <motion.div
    variants={{
      hidden: { opacity: 0, y: 30 },
      visible: { opacity: 1, y: 0 },
    }}
    transition={{ duration: 0.5, ease: "easeInOut" }}
    className={`relative flex h-full flex-col overflow-hidden rounded-3xl border border-white/10 bg-gradient-to-br from-white/5 to-white/[0.02] shadow-xl shadow-black/20 backdrop-blur-lg ${className}`}
  >
    {children}
  </motion.div>
);

// --- ENHANCED IMAGE CAROUSEL WITH SMOOTH TRANSITIONS ---

const ImageCarousel: React.FC<{
  images: { src: string; alt: string }[];
}> = ({ images }) => {
  const [currentIndex, setCurrentIndex] = useState(0);

  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentIndex((prev) => (prev + 1) % images.length);
    }, 4000);
    return () => clearInterval(timer);
  }, [images.length]);

  return (
    <div className="relative mt-auto h-[320px] w-full flex-1 md:h-[380px]">
      <div className="group relative h-full w-full cursor-pointer overflow-hidden rounded-xl border border-white/5 bg-slate-900/50">
        <AnimatePresence initial={false}>
          <motion.div
            key={currentIndex}
            initial={{ opacity: 0, x: 30 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -30 }}
            transition={{ duration: 0.7, ease: [0.32, 0.72, 0, 1] }}
            className="absolute h-full w-full"
          >
            <Image
              src={images[currentIndex].src}
              alt={images[currentIndex].alt}
              fill
              className="object-cover object-top"
              priority
            />
          </motion.div>
        </AnimatePresence>
        <div className="absolute inset-0 bg-gradient-to-t from-black/40 via-transparent to-black/10" />
      </div>
      <div className="absolute -bottom-7 left-1/2 flex -translate-x-1/2 transform gap-2 py-2">
        {images.map((_, index) => (
          <button
            key={index}
            onClick={() => setCurrentIndex(index)}
            className={`h-2 w-2 rounded-full transition-all duration-300 ${
              index === currentIndex
                ? "w-5 bg-[#01BBFF]"
                : "bg-white/30 hover:bg-white/60"
            }`}
            aria-label={`View image ${index + 1}`}
          />
        ))}
      </div>
    </div>
  );
};

// --- DATA-DRIVEN STRUCTURE FOR THE INTERNET SECTION ---

const mainFeaturesData = [
  {
    icon: Search,
    title: "Always Up-to-Date",
    subtitle: "Web Search",
    description:
      "Most AI models have a knowledge cutoff, but GAIA can fetch real-time updates from the internet. Whether it's breaking news or the latest industry trends, you'll always have access to the most up-to-date insights.",
    features: [
      "Real-time answers, never outdated.",
      "Instant fact-checking from live sources.",
      "Goes beyond preloaded AI knowledge.",
    ],
    component: (
      <ImageCarousel
        images={[
          { src: "/landing/web/0.webp", alt: "Web search Screenshot weather" },
          { src: "/landing/web/1.webp", alt: "Web search Screenshot 1" },
          { src: "/landing/web/2.webp", alt: "Web search Screenshot 2" },
          { src: "/landing/web/3.webp", alt: "Web search Screenshot 3" },
          { src: "/landing/web/4.webp", alt: "Web search Screenshot 4" },
        ]}
      />
    ),
  },
  {
    icon: ExternalLink,
    title: "Let AI Read for You",
    subtitle: "Fetch Webpages",
    description:
      "Ever wished your AI assistant could read and understand content from webpages? GAIA fetches and processes web content, so you get instant insights without endless scrolling.",
    features: [
      "Instantly fetch and summarize any webpage.",
      "No more searching through clutter—get key insights fast.",
      "Works on articles, research papers, blogs, and more.",
    ],
    component: (
      <ImageCarousel
        images={[
          {
            src: "/landing/web/fetch/0.webp",
            alt: "Fetch Webpage Screenshot 4",
          },
          {
            src: "/landing/web/fetch/1.webp",
            alt: "Fetch Webpage Screenshot 1",
          },
          {
            src: "/landing/web/fetch/3.webp",
            alt: "Fetch Webpage Screenshot 3",
          },
          {
            src: "/landing/web/fetch/2.webp",
            alt: "Fetch Webpage Screenshot 2",
          },
        ]}
      />
    ),
  },
];

// --- MAIN COMPONENT WITH ALL ENHANCEMENTS ---

export default function Internet() {
  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: { staggerChildren: 0.15 },
    },
  };

  const itemVariants = {
    hidden: { opacity: 0, y: 20 },
    visible: { opacity: 1, y: 0, transition: { duration: 0.5 } },
  };

  return (
    <div className="relative min-h-screen overflow-hidden bg-[radial-gradient(ellipse_at_top_left,_#0f0f0f,_#09090b)] bg-cover bg-fixed bg-no-repeat">
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_50%_50%,rgba(1,187,255,0.05),transparent_50%)]" />
      <div className="absolute inset-0 bg-[linear-gradient(to_right,#80808008_1px,transparent_1px),linear-gradient(to_bottom,#80808008_1px,transparent_1px)] bg-[size:32px_32px]" />

      <motion.div
        initial="hidden"
        whileInView="visible"
        viewport={{ once: true, amount: 0.1 }}
        variants={containerVariants}
        className="relative z-10 container mx-auto max-w-7xl px-4 py-24"
      >
        <div className="mb-16 text-center">
          <motion.div variants={itemVariants}>
            <SectionChip icon={Globe} text="Live Web Intelligence" />
          </motion.div>
          <motion.h1
            variants={itemVariants}
            className="relative z-10 bg-gradient-to-br from-white via-gray-200 to-gray-400 bg-clip-text text-4xl leading-tight font-bold text-transparent md:text-5xl lg:text-6xl"
          >
            Real-Time Internet Access
          </motion.h1>
          <motion.p
            variants={itemVariants}
            className="mx-auto mt-4 max-w-3xl text-lg leading-relaxed text-gray-400 md:text-xl"
          >
            Break free from knowledge cutoffs. GAIA accesses live information,
            delivering up-to-the-minute insights and answers.
          </motion.p>
        </div>

        <motion.div
          variants={containerVariants}
          className="grid grid-cols-1 gap-4 md:gap-6 lg:grid-cols-2"
        >
          {mainFeaturesData.map((card, index) => (
            <FeatureCard key={index}>
              <div className="flex h-full flex-col p-6 md:p-8">
                <motion.div variants={itemVariants} className="mb-6">
                  <div className="mb-4 flex items-center gap-4">
                    <div className="flex h-12 w-12 items-center justify-center rounded-xl border border-white/10 bg-slate-800/70">
                      <card.icon className="h-6 w-6 text-[#01BBFF]" />
                    </div>
                    <div>
                      <h3 className="text-xl font-bold text-white md:text-2xl">
                        {card.title}
                      </h3>
                      <p className="text-sm font-medium text-[#01BBFF]">
                        {card.subtitle}
                      </p>
                    </div>
                  </div>
                  <p className="text-sm text-gray-400 md:text-base">
                    {card.description}
                  </p>
                </motion.div>
                <motion.ul variants={itemVariants} className="mb-8 space-y-3">
                  {card.features.map((feature, i) => (
                    <li key={i} className="flex items-start gap-3">
                      <CheckCircle2 className="mt-0.5 h-4 w-4 flex-shrink-0 text-[#01BBFF]" />
                      <span className="text-sm text-gray-300">{feature}</span>
                    </li>
                  ))}
                </motion.ul>
                <motion.div variants={itemVariants} className="mt-auto flex-1">
                  {card.component}
                </motion.div>
              </div>
            </FeatureCard>
          ))}
        </motion.div>
      </motion.div>
    </div>
  );
}
