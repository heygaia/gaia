import { apiService } from "@/lib/api";

export interface ModelInfo {
  model_id: string;
  name: string;
  provider: string;
  description?: string;
  max_tokens: number;
  supports_streaming: boolean;
  supports_function_calling: boolean;
  available_in_plans: string[];
  is_default: boolean;
}

export interface ModelsListResponse {
  models: ModelInfo[];
}

export interface ModelSelectionRequest {
  model_id: string;
}

export interface ModelSelectionResponse {
  success: boolean;
  message: string;
  selected_model: ModelInfo;
}

export const fetchAvailableModels = async (): Promise<ModelInfo[]> => {
  const response = await apiService.get<ModelInfo[]>("/chat-models", {
    errorMessage: "Failed to fetch available models",
    silent: true,
  });
  return response;
};

export const selectModel = async (
  modelId: string,
): Promise<ModelSelectionResponse> => {
  return apiService.put<ModelSelectionResponse>(
    "/chat-models/select",
    {
      model_id: modelId,
    },
    {
      errorMessage: "Failed to select model",
    },
  );
};

export const fetchModelDetails = async (
  modelId: string,
): Promise<ModelInfo> => {
  return apiService.get<ModelInfo>(`/chat-models/${modelId}`, {
    errorMessage: "Failed to fetch model details",
  });
};
