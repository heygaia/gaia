"use client";

import { Chip } from "@heroui/chip";
import { ArrowUpRight } from "lucide-react";
import Image from "next/image";

import { Gmail } from "@/components";

export default function WorkflowCard() {
  return (
    <div className="group relative flex aspect-square cursor-pointer flex-col rounded-2xl border-1 border-zinc-800 bg-zinc-800 p-4 transition duration-300 hover:scale-105 hover:border-zinc-600">
      <ArrowUpRight
        className="absolute top-4 right-4 text-foreground-400 opacity-0 transition group-hover:opacity-100"
        width={25}
        height={25}
      />

      <div className="flex items-center gap-3">
        <Image
          src="/icons/notion.webp"
          alt="Image"
          width={40}
          className="h-[40px] object-contain"
          height={40}
        />

        <Image
          src="/icons/google_docs.webp"
          alt="Image"
          width={40}
          className="h-[40px] object-contain"
          height={40}
        />
      </div>
      <h3 className="mt-4">Title</h3>
      <div className="flex-1 text-sm text-foreground-500">
        Lorem ipsum dolor, sit amet consectetur adipisicing elit. Et, eum!
      </div>

      <div className="flex w-full items-center justify-between">
        <Chip
          size="sm"
          startContent={<Gmail width={15} />}
          className="flex gap-1 px-2!"
        >
          on new emails
        </Chip>
        {/* <Chip
          size="sm"
          startContent={<CalendarIcon width={15} />}
          className="flex gap-1 px-2!"
        >
          Daily at 9:00 am
        </Chip> */}
        <Chip color="success" variant="flat" size="sm">
          Activated
        </Chip>
      </div>
    </div>
  );
}
