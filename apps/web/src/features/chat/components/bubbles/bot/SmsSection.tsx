import { Chip } from "@heroui/chip";
import { Divider } from "@heroui/divider";
import { Message01Icon } from "@icons";
import { ToolCard } from "@/config/openui/primitives/ToolCard";
import { ToolInset } from "@/config/openui/primitives/ToolInset";
import type { SmsData } from "@/types/features/toolDataTypes";

function batchColor(
  status?: string,
): "primary" | "success" | "danger" | "default" {
  if (status === "completed") return "success";
  if (status === "canceled") return "danger";
  if (status === undefined) return "default";
  return "primary";
}

function messageColor(
  status: string,
): "primary" | "success" | "warning" | "danger" | "default" {
  if (status === "delivered") return "success";
  if (status === "failed" || status === "canceled") return "danger";
  if (status === "delivery_unconfirmed") return "warning";
  if (status === "sent") return "primary";
  return "default";
}

export function SmsSection({ sms_data }: { sms_data: SmsData }) {
  const {
    batch_id,
    status,
    recipient_count,
    messages,
    rejected,
    counts,
    total,
  } = sms_data;
  const delivered = counts?.delivered;
  const headline =
    recipient_count !== undefined
      ? `${recipient_count} recipient${recipient_count === 1 ? "" : "s"}`
      : `${total ?? 0} messages`;
  return (
    <div className="mt-3 w-full">
      <ToolCard
        title={
          <span className="flex items-center gap-2">
            <Message01Icon className="h-4 w-4 flex-shrink-0" />
            SMS
          </span>
        }
        subtitle={headline}
      >
        <ToolInset>
          <div className="flex items-center justify-between gap-3">
            <Chip color={batchColor(status)} variant="flat" size="sm">
              {status ?? "sent"}
            </Chip>
            {delivered !== undefined && (
              <span className="text-xs text-zinc-400">
                {delivered} delivered
              </span>
            )}
          </div>
          {(messages?.length ?? 0) + (rejected?.length ?? 0) > 0 && (
            <Divider className="my-2" />
          )}
          <div className="space-y-1.5">
            {messages?.map((m) => (
              <div
                key={m.text_message_id}
                className="flex items-center justify-between gap-3"
              >
                <span className="truncate text-xs text-zinc-300">
                  {m.to_phone_number}
                </span>
                <Chip color={messageColor(m.status)} variant="flat" size="sm">
                  {m.status}
                </Chip>
              </div>
            ))}
            {rejected?.map((r) => (
              <div
                key={r.to_phone_number}
                className="flex items-center justify-between gap-3"
              >
                <span className="truncate text-xs text-zinc-300">
                  {r.to_phone_number}
                </span>
                <Chip color="danger" variant="flat" size="sm" title={r.reason}>
                  rejected
                </Chip>
              </div>
            ))}
          </div>
          <span className="mt-2 block truncate text-xs text-zinc-500">
            {batch_id}
          </span>
        </ToolInset>
      </ToolCard>
    </div>
  );
}
