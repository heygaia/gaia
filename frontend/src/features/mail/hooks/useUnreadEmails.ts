import { useQuery } from "@tanstack/react-query";

import { apiService } from "@/lib/api";
import { EmailData } from "@/types/features/mailTypes";

interface UnreadEmailsResponse {
  messages: EmailData[];
  nextPageToken?: string;
}

/**
 * Hook to fetch unread emails
 */
export const useUnreadEmails = (limit: number = 20) => {
  return useQuery({
    queryKey: ["unread-emails", limit],
    queryFn: async (): Promise<EmailData[]> => {
      const response = await apiService.get<UnreadEmailsResponse>(
        `/gmail/search?is_read=false&max_results=${limit}`,
        {
          errorMessage: "Failed to fetch unread emails",
          silent: true,
        },
      );
      return response.messages || [];
    },
    staleTime: 2 * 60 * 1000, // 2 minutes
    gcTime: 5 * 60 * 1000, // 5 minutes
    retry: 2,
    retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),
  });
};
