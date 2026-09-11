import type { Schema } from "@shared/api/generated";
import { apiService } from "@/lib/api/service";

export type ToolInfo = Schema<"ToolInfo">;

export type ToolsListResponse = Schema<"ToolsListResponse">;

export const fetchAvailableTools = async (): Promise<ToolsListResponse> => {
  return apiService.get<ToolsListResponse>("/tools", {
    errorMessage: "Failed to fetch available tools",
    silent: true,
  });
};
