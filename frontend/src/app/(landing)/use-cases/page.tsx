"use client";

import { Chip } from "@heroui/chip";
import { useEffect, useState } from "react";

import Spinner from "@/components/ui/shadcn/spinner";
import UseCaseCard from "@/features/use-cases/components/UseCaseCard";
import {
  type UseCase,
  useCasesData,
} from "@/features/use-cases/constants/dummy-data";
import {
  CommunityWorkflow,
  workflowApi,
} from "@/features/workflows/api/workflowApi";
import CommunityWorkflowCard from "@/features/workflows/components/CommunityWorkflowCard";

export default function UseCasesPage() {
  const [selectedCategory, setSelectedCategory] = useState("all");
  const [communityWorkflows, setCommunityWorkflows] = useState<
    CommunityWorkflow[]
  >([]);
  const [isLoadingCommunity, setIsLoadingCommunity] = useState(false);

  const allCategories = [
    "all",
    "Students",
    "Founders",
    "Engineering",
    "Marketing",
    "Knowledge Workers",
    "Business & Ops",
    "community",
  ];

  const filteredUseCases =
    selectedCategory === "all"
      ? useCasesData
      : selectedCategory === "community"
        ? []
        : useCasesData.filter((useCase: UseCase) =>
            useCase.categories?.includes(selectedCategory),
          );

  // Load community workflows
  useEffect(() => {
    const loadCommunityWorkflows = async () => {
      if (selectedCategory === "community" || selectedCategory === "all") {
        setIsLoadingCommunity(true);
        try {
          const response = await workflowApi.getCommunityWorkflows(8, 0);
          setCommunityWorkflows(response.workflows);
        } catch (error) {
          console.error("Error loading community workflows:", error);
        } finally {
          setIsLoadingCommunity(false);
        }
      }
    };

    loadCommunityWorkflows();
  }, [selectedCategory]);

  const scrollToCommunity = () => {
    const element = document.getElementById("community-section");
    if (element) {
      element.scrollIntoView({ behavior: "smooth" });
    }
  };

  return (
    <div className="min-h-screen">
      <div className="container mx-auto px-6 pt-24 pb-8">
        <div className="mb-8 text-center">
          <h1 className="mb-4 text-5xl font-bold">Use Cases</h1>
          <p className="mx-auto max-w-3xl text-xl text-foreground-500">
            Discover powerful automation templates and AI prompts to streamline
            your workflow
          </p>
        </div>

        <div className="mb-6 flex flex-wrap justify-center gap-2">
          {allCategories.map((category) => (
            <Chip
              key={category as string}
              variant={selectedCategory === category ? "solid" : "flat"}
              color={selectedCategory === category ? "primary" : "default"}
              className="cursor-pointer capitalize"
              size="lg"
              onClick={() => {
                if (category === "community") {
                  setSelectedCategory(category as string);
                  // Small delay to let state update before scrolling
                  setTimeout(scrollToCommunity, 100);
                } else {
                  setSelectedCategory(category as string);
                }
              }}
            >
              {category === "all"
                ? "All"
                : category === "community"
                  ? "By the Community"
                  : (category as string)}
            </Chip>
          ))}
        </div>

        {/* Regular use cases */}
        {selectedCategory !== "community" && (
          <div className="mx-auto mb-16 grid max-w-7xl grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
            {filteredUseCases.map((useCase: UseCase, index: number) => (
              <UseCaseCard
                key={useCase.published_id || index}
                title={useCase.title || ""}
                description={useCase.description || ""}
                action_type={useCase.action_type || "prompt"}
                integrations={useCase.integrations || []}
                prompt={useCase.prompt}
              />
            ))}
          </div>
        )}

        {/* Community workflows section */}
        {(selectedCategory === "all" || selectedCategory === "community") && (
          <div id="community-section" className="space-y-6">
            <div className="text-center">
              <h2 className="mb-2 text-3xl font-bold">By the Community</h2>
              <p className="mx-auto max-w-2xl text-lg text-foreground-500">
                Discover workflows created and shared by our community of users
              </p>
            </div>

            {isLoadingCommunity ? (
              <div className="flex h-48 items-center justify-center">
                <Spinner />
              </div>
            ) : communityWorkflows.length === 0 ? (
              <div className="flex h-48 items-center justify-center">
                <div className="text-lg text-foreground-500">
                  No community workflows available yet
                </div>
              </div>
            ) : (
              <div className="mx-auto grid max-w-7xl grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
                {communityWorkflows.map((workflow) => (
                  <CommunityWorkflowCard
                    key={workflow.id}
                    workflow={workflow}
                  />
                ))}
              </div>
            )}
          </div>
        )}

        {/* No results */}
        {selectedCategory !== "community" &&
          selectedCategory !== "all" &&
          filteredUseCases.length === 0 && (
            <div className="flex h-48 items-center justify-center">
              <p className="text-lg text-foreground-500">
                No use cases found for this category
              </p>
            </div>
          )}
      </div>
    </div>
  );
}
