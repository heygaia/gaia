import { MessageType } from "@/types/features/convoTypes";
import { TOOLS_MESSAGE_KEYS } from "@/types/features/baseMessageRegistry";

/**
 * Parses stream data and accumulates tool data for multiple tool calls.
 *
 * ACCUMULATION STRATEGY:
 * - For tool data keys: Always accumulate as arrays to handle multiple calls
 * - For non-tool data: Direct replacement (response text, metadata, etc.)
 *
 * OPTIMIZATION: Since we always store tool data as arrays from the start,
 * we can safely use push() instead of spread operator for better performance.
 *
 * This ensures multiple tool calls create arrays: [data1, data2, data3]
 * and matches the backend accumulation behavior.
 */
export function parseStreamData(
  streamChunk: Partial<MessageType>,
  existingBotMessage?: MessageType | null,
): Partial<MessageType> {
  if (!streamChunk) return {};

  const result: Partial<MessageType> = {};

  // Dynamically copy all defined properties from streamChunk to result
  for (const [key, value] of Object.entries(streamChunk)) {
    if (value !== undefined) {
      // Check if this is a tool data key that needs accumulation
      if (
        TOOLS_MESSAGE_KEYS.includes(key as (typeof TOOLS_MESSAGE_KEYS)[number])
      ) {
        // Get existing data for this tool key
        const existingData = existingBotMessage?.[key as keyof MessageType];

        if (existingData) {
          // Since we always store as arrays, existingData is guaranteed to be an array
          const existingArray = existingData as unknown[];
          (result as Record<string, unknown>)[key] = [...existingArray, value];
        } else {
          // No existing data, start with array containing this value
          (result as Record<string, unknown>)[key] = [value];
        }
      } else {
        // Non-tool data, just copy directly
        (result as Record<string, unknown>)[key] = value;
      }
    }
  }

  return result;
}
