"use client";

import { Input } from "@heroui/react";

interface CustomResponseStyleInputProps {
  value: string;
  onChange: (value: string) => void;
  isDisabled: boolean;
}

export function CustomResponseStyleInput({
  value,
  onChange,
  isDisabled,
}: CustomResponseStyleInputProps) {
  return (
    <div className="space-y-1">
      <Input
        placeholder="Describe your preferred response style..."
        value={value}
        onChange={(e) => onChange(e.target.value)}
        isDisabled={isDisabled}
        classNames={{
          input: "bg-zinc-800/50 min-h-[36px] text-sm",
          inputWrapper: "bg-zinc-800/50 hover:bg-zinc-700/50",
        }}
      />
    </div>
  );
}
