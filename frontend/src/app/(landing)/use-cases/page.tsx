"use client";

import { useState } from "react";
import { Chip } from "@heroui/chip";
import UseCaseCard from "@/features/use-cases/components/UseCaseCard";
import dataJson from "@/features/use-cases/constants/data.json";

export default function UseCasesPage() {
  const [selectedCategory, setSelectedCategory] = useState("all");

  const data = dataJson as unknown as { templates: any[] };

  const allCategories = [
    "all",
    ...Array.from(
      new Set(data.templates.flatMap((item: any) => item.categories || [])),
    ),
  ];

  const filteredUseCases =
    selectedCategory === "all"
      ? data.templates
      : data.templates.filter((useCase: any) =>
          useCase.categories?.includes(selectedCategory),
        );

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
              onClick={() => setSelectedCategory(category as string)}
            >
              {category === "all" ? "All" : (category as string)}
            </Chip>
          ))}
        </div>

        <div className="mx-auto grid max-w-7xl grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
          {filteredUseCases.map((useCase: any, index: number) => (
            <UseCaseCard
              key={useCase.published_id || index}
              title={useCase.title || ""}
              description={useCase.description || ""}
              action_type={useCase.action_type || "prompt"}
              integrations={useCase.integrations || []}
            />
          ))}
        </div>

        {filteredUseCases.length === 0 && (
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
