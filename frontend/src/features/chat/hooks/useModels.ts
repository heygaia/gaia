import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";

import { fetchAvailableModels, selectModel, ModelInfo } from "../api/modelsApi";
import { useUser } from "@/features/auth/hooks/useUser";
import { setUser } from "@/redux/slices/userSlice";

export const useModels = () => {
  return useQuery({
    queryKey: ["models"],
    queryFn: fetchAvailableModels,
    staleTime: 5 * 60 * 1000, // 5 minutes
    gcTime: 10 * 60 * 1000, // 10 minutes
    refetchOnWindowFocus: false,
    refetchOnMount: false,
  });
};

export const useSelectModel = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: selectModel,
    onSuccess: (data) => {
      // Invalidate user data to refresh selected model
      queryClient.invalidateQueries({ queryKey: ["user"] });
    },
    onError: (error) => {
      toast.error("Failed to select model");
      console.error("Model selection error:", error);
    },
  });
};

export const useCurrentUserModel = (): ModelInfo | null => {
  const { data: models } = useModels();
  const user = useUser();

  return (
    models?.find((model) => model.model_id === user.selected_model) || null
  );
};
