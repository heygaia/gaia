/**
 * Data for the message being replied to.
 */
export interface ReplyToMessageData {
  id: string;
  content: string;
  role: "user" | "assistant";
}
