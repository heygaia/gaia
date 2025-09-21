"use client";

import { useEffect, useRef, useState } from "react";

import Spinner from "@/components/ui/shadcn/spinner";
import UseCaseSection from "@/features/use-cases/components/UseCaseSection";
import {
  CommunityWorkflow,
  workflowApi,
} from "@/features/workflows/api/workflowApi";
import CommunityWorkflowCard from "@/features/workflows/components/CommunityWorkflowCard";

export default function UseCasesPage() {
  const [communityWorkflows, setCommunityWorkflows] = useState<
    CommunityWorkflow[]
  >([]);
  const contentRef = useRef(null);

  const [isLoadingCommunity, setIsLoadingCommunity] = useState(false);

  // Load community workflows
  useEffect(() => {
    const loadCommunityWorkflows = async () => {
      setIsLoadingCommunity(true);
      try {
        const response = await workflowApi.getCommunityWorkflows(8, 0);
        setCommunityWorkflows(response.workflows);
      } catch (error) {
        console.error("Error loading community workflows:", error);
      } finally {
        setIsLoadingCommunity(false);
      }
    };

    loadCommunityWorkflows();
  }, []);

  return (
    <div className="min-h-screen" ref={contentRef}>
      <div className="container mx-auto px-6 pt-30 pb-8">
        <div className="mb-8 text-center">
          <h1 className="mb-4 text-5xl font-bold">Use Cases</h1>
          <p className="mx-auto max-w-3xl text-xl text-foreground-500">
            Discover powerful automation templates and AI prompts to streamline
            your workflow
          </p>
        </div>

        <UseCaseSection dummySectionRef={contentRef} />

        <div id="community-section" className="mt-14 space-y-6">
          <div className="text-center">
            <h2 className="mb-2 text-4xl font-bold">By the Community</h2>
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
                <CommunityWorkflowCard key={workflow.id} workflow={workflow} />
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
