import type { Schema } from "@shared/api/generated";
import { apiService } from "@/lib/api/service";

export type VoiceOption = Schema<"VoiceOption">;

export type VoiceListResponse = Schema<"VoiceListResponse">;

export const voiceApi = {
  getVoices: async (): Promise<VoiceListResponse> => {
    return apiService.get<VoiceListResponse>("/voice/voices", {
      errorMessage: "Failed to load voices",
    });
  },

  selectVoice: async (
    voiceId: string,
  ): Promise<{ selected_voice_id: string }> => {
    return apiService.put(
      "/voice/voices/selected",
      { voice_id: voiceId },
      { errorMessage: "Failed to update voice" },
    );
  },

  starVoice: async (
    voiceId: string,
    starred: boolean,
  ): Promise<{ starred_voice_ids: string[] }> => {
    return apiService.put(
      `/voice/voices/${voiceId}/star`,
      { starred },
      { errorMessage: "Failed to update starred voices" },
    );
  },
};
