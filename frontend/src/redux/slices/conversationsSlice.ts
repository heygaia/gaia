import { createAsyncThunk, createSlice, PayloadAction } from "@reduxjs/toolkit";

import { chatApi, type Conversation } from "@/features/chat/api/chatApi";
import { putConversationsBulk } from "@/services/indexedDb/chatDb";

// Re-export the Conversation type for compatibility
export type { Conversation };

// Define the Pagination metadata for conversations.
export interface ConversationPaginationMeta {
  total: number;
  page: number;
  limit: number;
  total_pages: number;
}

// Define the slice state.
interface ConversationState {
  conversations: Conversation[];
  paginationMeta: ConversationPaginationMeta | null;
  loading: boolean;
  error: string | null;
}

// Set the initial state.
const initialState: ConversationState = {
  conversations: [],
  paginationMeta: null,
  loading: false,
  error: null,
};

// Async thunk to fetch conversations.
export const fetchConversations = createAsyncThunk<
  {
    conversations: Conversation[];
    paginationMeta: ConversationPaginationMeta;
    append: boolean;
  },
  { page?: number; limit?: number; append?: boolean },
  { rejectValue: string }
>(
  "conversations/fetchConversations",
  async ({ page = 1, limit = 20, append = true }, { rejectWithValue }) => {
    try {
      const data = await chatApi.fetchConversations(page, limit);
      // Persist into IndexedDB in background
      if (data?.conversations && data.conversations.length > 0) {
        putConversationsBulk(data.conversations as any).catch((e) =>
          console.error("putConversationsBulk error:", e),
        );
      }
      return {
        conversations: data.conversations ?? [],
        paginationMeta: {
          total: data.total ?? 0,
          page: data.page ?? 1,
          limit: data.limit ?? limit,
          total_pages: data.total_pages ?? 1,
        },
        append,
      };
    } catch (error: unknown) {
      return rejectWithValue(
        (error as Error).message || "Failed to fetch conversations",
      );
    }
  },
);

// Create the slice.
const conversationSlice = createSlice({
  name: "conversations",
  initialState,
  reducers: {
    // Optional: Synchronous actions if you need them.
    setConversations: (state, action: PayloadAction<Conversation[]>) => {
      state.conversations = action.payload;
    },
    clearConversations: (state) => {
      state.conversations = [];
      state.paginationMeta = null;
    },
  },
  extraReducers: (builder) => {
    builder.addCase(fetchConversations.pending, (state) => {
      state.loading = true;
      state.error = null;
    });
    builder.addCase(fetchConversations.fulfilled, (state, action) => {
      state.loading = false;
      const { conversations, paginationMeta, append } = action.payload;
      if (append) {
        // Merge the existing conversations with the new ones while deduplicating.
        const combined = [...state.conversations, ...conversations];
        const uniqueMap = new Map(
          combined.map((conv) => [conv.conversation_id, conv]),
        );
        state.conversations = Array.from(uniqueMap.values());
      } else {
        state.conversations = conversations;
      }
      state.paginationMeta = paginationMeta;
    });
    builder.addCase(fetchConversations.rejected, (state, action) => {
      state.loading = false;
      state.error = action.payload ?? "Error fetching conversations";
    });
  },
});

// Export actions if needed.
export const { setConversations, clearConversations } =
  conversationSlice.actions;

// Export the reducer.
export default conversationSlice.reducer;
