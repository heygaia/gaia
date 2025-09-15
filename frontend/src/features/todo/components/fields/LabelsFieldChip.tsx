"use client";

import { Button } from "@heroui/button";
import { Input } from "@heroui/input";
import { Hash, Plus, X } from "lucide-react";
import { useState } from "react";

import BaseFieldChip from "./BaseFieldChip";

interface LabelsFieldChipProps {
  value: string[];
  onChange: (labels: string[]) => void;
  className?: string;
}

export default function LabelsFieldChip({
  value = [],
  onChange,
  className,
}: LabelsFieldChipProps) {
  const [newLabel, setNewLabel] = useState("");

  const displayValue =
    value.length > 0
      ? `${value.length} label${value.length > 1 ? "s" : ""}`
      : undefined;

  const handleAddLabel = () => {
    const trimmedLabel = newLabel.trim();
    if (trimmedLabel && !value.includes(trimmedLabel)) {
      onChange([...value, trimmedLabel]);
      setNewLabel("");
    }
  };

  const handleRemoveLabel = (labelToRemove: string) => {
    onChange(value.filter((label) => label !== labelToRemove));
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") {
      e.preventDefault();
      handleAddLabel();
    }
  };

  return (
    <BaseFieldChip
      label="Labels"
      value={displayValue}
      placeholder="Labels"
      icon={<Hash size={14} />}
      variant={value.length > 0 ? "primary" : "default"}
      className={className}
    >
      <div className="p-1">
        <div className="border-0 bg-zinc-900 p-3">
          {/* Add new label */}
          <div className="mb-1">
            <div className="flex gap-2">
              <div className="relative flex-1">
                <Hash
                  size={14}
                  className="absolute top-1/2 left-3 z-10 -translate-y-1/2 transform text-zinc-500"
                />
                <Input
                  placeholder="Add label..."
                  value={newLabel}
                  onChange={(e) => setNewLabel(e.target.value)}
                  onKeyDown={handleKeyDown}
                  size="sm"
                  aria-label="Add new label"
                  classNames={{
                    input:
                      "pl-8 text-sm text-zinc-200 placeholder:text-zinc-500",
                    inputWrapper:
                      "border-0 bg-zinc-800 hover:bg-zinc-700 focus:bg-zinc-700 data-[focus=true]:bg-zinc-700",
                  }}
                />
              </div>
              <Button
                size="sm"
                variant="light"
                isDisabled={!newLabel.trim() || value.includes(newLabel.trim())}
                onPress={handleAddLabel}
                className={`h-8 min-w-8 border-0 p-0 ${
                  !newLabel.trim() || value.includes(newLabel.trim())
                    ? "bg-zinc-800 text-zinc-600 hover:bg-zinc-700"
                    : "bg-zinc-800 text-zinc-200 hover:bg-zinc-700"
                }`}
              >
                <Plus size={14} />
              </Button>
            </div>
          </div>

          {/* Existing labels */}
          {value.length > 0 && (
            <div className="flex flex-wrap gap-1">
              {value.map((label) => (
                <div
                  key={label}
                  className="flex items-center gap-1 rounded-md bg-zinc-800 px-2 py-1 text-sm text-zinc-300 hover:bg-zinc-700"
                >
                  <Hash size={12} />
                  {label}
                  <Button
                    variant="light"
                    size="sm"
                    onPress={() => handleRemoveLabel(label)}
                    className="h-4 w-4 min-w-4 border-0 p-0 text-zinc-400 hover:text-zinc-200"
                  >
                    <X size={10} />
                  </Button>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Quick actions */}
        {value.length > 0 && (
          <>
            <div className="my-1 h-px bg-zinc-700" />
            <div
              onClick={() => onChange([])}
              className="flex cursor-pointer items-center gap-2 rounded-md px-3 py-2 text-red-400 transition-colors hover:bg-zinc-800"
            >
              <X size={14} />
              Clear all labels
            </div>
          </>
        )}
      </div>
    </BaseFieldChip>
  );
}
