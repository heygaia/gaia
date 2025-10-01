import { Chip } from "@heroui/chip";
import { AnimatePresence, motion } from "framer-motion";
import { gsap } from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import { useCallback, useEffect, useState } from "react";

import UseCaseCard from "@/features/use-cases/components/UseCaseCard";
import {
  type UseCase,
  useCasesData,
} from "@/features/use-cases/constants/dummy-data";
import { Workflow } from "@/features/workflows/api/workflowApi";
import UserWorkflowCard from "@/features/workflows/components/UserWorkflowCard";
import { useWorkflows } from "@/features/workflows/hooks/useWorkflows";

// Register GSAP plugin
gsap.registerPlugin(ScrollTrigger);

export default function UseCaseSection({
  dummySectionRef,
  hideUserWorkflows = false,
}: {
  dummySectionRef: React.RefObject<HTMLDivElement | null>;
  hideUserWorkflows?: boolean;
}) {
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);
  const { workflows, isLoading: isLoadingWorkflows } = useWorkflows();

  // Find scroll container - memoized to prevent effect re-runs
  const getScrollContainer = useCallback(() => {
    let current = dummySectionRef.current?.parentElement;
    while (current) {
      const styles = window.getComputedStyle(current);
      if (styles.overflowY === "auto" || styles.overflowY === "scroll") {
        return current;
      }
      current = current.parentElement;
    }
    return null;
  }, [dummySectionRef]);

  // Simple GSAP ScrollTrigger
  useEffect(() => {
    if (!dummySectionRef.current) return;

    const scrollContainer = getScrollContainer();
    if (!scrollContainer) return;

    const trigger = ScrollTrigger.create({
      trigger: dummySectionRef.current,
      scroller: scrollContainer,
      start: "top 50%",
      end: "bottom-=10 40%",
      // snap: {
      //   snapTo: 1, // snap to the closest section (1 means each one)
      //   duration: 0.4, // lower = faster snapping (default is 0.5)
      // },

      onEnter: () => {
        // Scrolling down - auto select featured
        if (selectedCategory === null) setSelectedCategory("featured");
      },

      onLeaveBack: () => {
        // Scrolling up - auto unselect
        if (selectedCategory !== null) setSelectedCategory(null);
      },
    });

    return () => trigger.kill();
  }, [selectedCategory, dummySectionRef, getScrollContainer]);

  const allCategories = [
    "all",
    "featured",
    "workflows",
    "Students",
    "Founders",
    "Engineering",
    "Marketing",
    "Knowledge Workers",
    "Business & Ops",
  ];

  if (hideUserWorkflows) allCategories.splice(2, 1);

  const filteredUseCases =
    selectedCategory === null
      ? []
      : selectedCategory === "all"
        ? useCasesData
        : useCasesData.filter((useCase: UseCase) =>
          useCase.categories?.includes(selectedCategory),
        );

  const handleCategoryClick = (category: string) => {
    const wasSelected = selectedCategory === category;
    const scrollContainer = getScrollContainer();

    if (!scrollContainer) return;

    if (wasSelected) {
      // Unselecting: scroll to top
      setSelectedCategory(null);
      gsap.to(scrollContainer, {
        scrollTop: 0,
        duration: 0.5,
        ease: "power2.out",
      });
    } else {
      // Selecting: scroll to show cards
      setSelectedCategory(category);

      // Small delay to let state update
      setTimeout(() => {
        if (!dummySectionRef.current) return;

        const sectionRect = dummySectionRef.current.getBoundingClientRect();
        const containerRect = scrollContainer.getBoundingClientRect();
        const currentScrollTop = scrollContainer.scrollTop;
        const targetScrollTop =
          currentScrollTop + (sectionRect.bottom - containerRect.bottom) + 100;

        gsap.to(scrollContainer, {
          scrollTop: Math.max(0, targetScrollTop),
          duration: 0.5,
          ease: "power2.out",
        });
      }, 50);
    }
  };

  // Cleanup
  useEffect(() => {
    return () => {
      ScrollTrigger.getAll().forEach((trigger) => trigger.kill());
    };
  }, []);

  return (
    <div className="w-full max-w-7xl" ref={dummySectionRef}>
      <div className="mb-6 flex flex-wrap justify-center gap-2">
        {allCategories.map((category) => (
          <Chip
            key={category as string}
            variant={selectedCategory === category ? "solid" : "flat"}
            color={selectedCategory === category ? "primary" : "default"}
            className={`cursor-pointer capitalize ${selectedCategory === category ? "" : "text-foreground-500"} font-light!`}
            size="lg"
            onClick={() => handleCategoryClick(category as string)}
          >
            {category === "all"
              ? "All"
              : category === "featured"
                ? "Featured"
                : category === "workflows"
                  ? "Your Workflows"
                  : (category as string)}
          </Chip>
        ))}
      </div>

      <AnimatePresence mode="wait">
        {/* Render Use Cases */}
        {filteredUseCases.length > 0 &&
          selectedCategory !== null &&
          selectedCategory !== "workflows" && (
            <motion.div
              key={selectedCategory}
              className="mx-auto grid max-w-7xl grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              transition={{ duration: 0.3, ease: "easeOut" }}
            >
              {filteredUseCases
                .slice(0, 8)
                .map((useCase: UseCase, index: number) => (
                  <motion.div
                    key={useCase.published_id || index}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{
                      duration: 0.3,
                      delay: index * 0.05, // Stagger animation
                      ease: "easeOut",
                    }}
                  >
                    <UseCaseCard
                      title={useCase.title || ""}
                      description={useCase.description || ""}
                      action_type={useCase.action_type || "prompt"}
                      integrations={useCase.integrations || []}
                      prompt={useCase.prompt}
                    />
                  </motion.div>
                ))}
            </motion.div>
          )}

        {/* Render User Workflows */}
        {selectedCategory === "workflows" &&
          !isLoadingWorkflows &&
          workflows.length > 0 && (
            <motion.div
              key="workflows"
              className="mx-auto grid max-w-7xl grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              transition={{ duration: 0.3, ease: "easeOut" }}
            >
              {workflows
                .slice(0, 8)
                .map((workflow: Workflow, index: number) => (
                  <motion.div
                    key={workflow.id}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{
                      duration: 0.3,
                      delay: index * 0.05, // Stagger animation
                      ease: "easeOut",
                    }}
                  >
                    <UserWorkflowCard workflow={workflow} />
                  </motion.div>
                ))}
            </motion.div>
          )}
      </AnimatePresence>

      {/* Empty states */}
      {filteredUseCases.length === 0 &&
        selectedCategory !== null &&
        selectedCategory !== "workflows" && (
          <div className="flex h-48 items-center justify-center"></div>
        )}

      {selectedCategory === "workflows" &&
        !isLoadingWorkflows &&
        workflows.length === 0 && (
          <div className="flex h-48 items-center justify-center">
            <div className="text-center">
              <p className="text-lg text-foreground-500">No workflows found</p>
              <p className="text-sm text-foreground-600">
                Create your first workflow to get started
              </p>
            </div>
          </div>
        )}

      {selectedCategory === "workflows" && isLoadingWorkflows && (
        <div className="flex h-48 items-center justify-center">
          <div className="text-center">
            <p className="text-lg text-foreground-500">Loading workflows...</p>
          </div>
        </div>
      )}
    </div>
  );
}
