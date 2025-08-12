"use client";

import { Button } from "@heroui/button";
import { useDisclosure } from "@heroui/modal";
import { PlusIcon } from "lucide-react";
import WorkflowCard from "./WorkflowCard";
import CreateWorkflowModal from "./CreateWorkflowModal";

export default function WorkflowPage() {
  const { isOpen, onOpen, onOpenChange } = useDisclosure();

  return (
    <div className="overflow-y-auto p-8 px-10">
      <div className="flex min-h-[50vh] flex-col gap-7">
        <div>
          <div className="flex w-full items-center justify-between">
            <h1>Your Workflows</h1>
            <Button
              color="primary"
              size="sm"
              startContent={<PlusIcon width={16} height={16} />}
              onPress={onOpen}
            >
              Create
            </Button>
          </div>
          <div className="text-foreground-400">
            Lorem ipsum dolor sit amet consectetur adipisicing elit. Doloribus,
            iste!
          </div>
        </div>

        <div className="grid grid-cols-5">
          <WorkflowCard />
        </div>
      </div>

      <div className="flex min-h-[50vh] flex-col">
        <h1>Explore</h1>
      </div>

      <CreateWorkflowModal isOpen={isOpen} onOpenChange={onOpenChange} />
    </div>
  );
}
