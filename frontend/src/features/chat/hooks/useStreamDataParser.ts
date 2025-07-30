import { MessageType } from "@/types/features/convoTypes";

export function parseStreamData(
  streamChunk: Partial<MessageType>,
): Partial<MessageType> {
  if (!streamChunk) return {};

  const result: Partial<MessageType> = {};

  // Dynamically copy all defined properties from streamChunk to result
  // This automatically handles any tool data without manual if conditions
  for (const [key, value] of Object.entries(streamChunk)) {
    if (value !== undefined) {
      // Type assertion is safe here since we're iterating over streamChunk properties
      (result as Record<string, unknown>)[key] = value;
    }
  }

  return result;
}
