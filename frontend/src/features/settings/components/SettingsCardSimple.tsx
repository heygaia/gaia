import { ReactNode } from "react";

interface SettingsCardSimpleProps {
  children: ReactNode;
  className?: string;
}

export function SettingsCardSimple({
  children,
  className = "",
}: SettingsCardSimpleProps) {
  return (
    <div
      className={`rounded-2xl bg-zinc-900 p-4 outline-1 outline-zinc-800 ${className}`}
    >
      {children}
    </div>
  );
}
