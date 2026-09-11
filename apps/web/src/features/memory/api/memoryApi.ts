import type { Schema } from "@shared/api/generated";
import { apiService } from "@/lib/api/service";

interface ListMemoriesParams {
  page?: number;
  pageSize?: number;
  category?: string;
}

export const memoryApi = {
  listMemories: async ({
    page = 1,
    pageSize = 20,
    category,
  }: ListMemoriesParams = {}): Promise<Schema<"MemoryListResponse">> => {
    const params = new URLSearchParams({
      page: String(page),
      page_size: String(pageSize),
    });
    if (category) params.set("category", category);
    return apiService.get<Schema<"MemoryListResponse">>(`/memory?${params}`, {
      silent: true,
    });
  },

  searchMemories: async (
    query: string,
    limit = 20,
  ): Promise<Schema<"MemorySearchResult">> => {
    const params = new URLSearchParams({ q: query, limit: String(limit) });
    return apiService.get<Schema<"MemorySearchResult">>(
      `/memory/search?${params}`,
      {
        silent: true,
      },
    );
  },

  getHistory: async (id: string): Promise<Schema<"MemorySearchResult">> => {
    return apiService.get<Schema<"MemorySearchResult">>(
      `/memory/${id}/history`,
      {
        silent: true,
      },
    );
  },

  getOverview: async (): Promise<Schema<"MemoryOverviewResponse">> => {
    return apiService.get<Schema<"MemoryOverviewResponse">>(
      "/memory/overview",
      {
        silent: true,
      },
    );
  },

  getTree: async (): Promise<Schema<"MemoryTreeResponse">> => {
    return apiService.get<Schema<"MemoryTreeResponse">>("/memory/tree", {
      silent: true,
    });
  },

  getGraph: async (): Promise<Schema<"MemoryGraphResponse">> => {
    return apiService.get<Schema<"MemoryGraphResponse">>("/memory/graph", {
      silent: true,
    });
  },

  getEpisodes: async (
    start: string,
    end: string,
  ): Promise<Schema<"MemoryEpisodesResponse">> => {
    const params = new URLSearchParams({ start, end });
    return apiService.get<Schema<"MemoryEpisodesResponse">>(
      `/memory/episodes?${params}`,
      { silent: true },
    );
  },

  getDocuments: async (): Promise<Schema<"MemoryDocumentsResponse">> => {
    return apiService.get<Schema<"MemoryDocumentsResponse">>(
      "/memory/documents",
      {
        silent: true,
      },
    );
  },

  updateDocument: async (
    docType: Schema<"MemoryDocType">,
    content: string,
  ): Promise<Schema<"MemoryDocument">> => {
    return apiService.put<Schema<"MemoryDocument">>(
      `/memory/documents/${docType}`,
      { content },
      { silent: true },
    );
  },

  createMemory: async (
    request: Schema<"CreateMemoryRequest">,
  ): Promise<Schema<"CreateMemoryResponse">> => {
    return apiService.post<Schema<"CreateMemoryResponse">>("/memory", request, {
      silent: true,
    });
  },

  updateMemory: async (
    id: string,
    content: string,
  ): Promise<Schema<"MemoryEntry">> => {
    return apiService.patch<Schema<"MemoryEntry">>(
      `/memory/${id}`,
      { content },
      { silent: true },
    );
  },

  deleteMemory: async (id: string): Promise<Schema<"DeleteMemoryResponse">> => {
    return apiService.delete<Schema<"DeleteMemoryResponse">>(`/memory/${id}`, {
      silent: true,
    });
  },

  deleteAllMemories: async (): Promise<Schema<"DeleteMemoryResponse">> => {
    return apiService.delete<Schema<"DeleteMemoryResponse">>("/memory", {
      silent: true,
    });
  },
};
