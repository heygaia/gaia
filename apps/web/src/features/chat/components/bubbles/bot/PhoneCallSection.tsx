import { Chip } from "@heroui/chip";
import { Call02Icon } from "@icons";
import { ToolCard } from "@/config/openui/primitives/ToolCard";
import { ToolInset } from "@/config/openui/primitives/ToolInset";
import type { PhoneCallData } from "@/types/features/toolDataTypes";

function statusColor(
  status: string,
): "primary" | "success" | "danger" | "default" {
  if (status === "completed") return "success";
  if (status === "error" || status === "canceled") return "danger";
  if (status === "unknown") return "default";
  return "primary";
}

export function PhoneCallSection({
  phone_call_data,
}: {
  phone_call_data: PhoneCallData;
}) {
  const { call_id, status, to_phone_number } = phone_call_data;
  return (
    <div className="mt-3 w-full">
      <ToolCard
        title={
          <span className="flex items-center gap-2">
            <Call02Icon className="h-4 w-4 flex-shrink-0" />
            Phone call
          </span>
        }
        subtitle={to_phone_number ?? undefined}
      >
        <ToolInset>
          <div className="flex items-center justify-between gap-3">
            <Chip color={statusColor(status)} variant="flat" size="sm">
              {status}
            </Chip>
            <span className="truncate text-xs text-zinc-500">{call_id}</span>
          </div>
        </ToolInset>
      </ToolCard>
    </div>
  );
}
