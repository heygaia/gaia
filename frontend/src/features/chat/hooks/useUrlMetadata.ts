import { useQuery, useQueryClient } from "@tanstack/react-query";

import { api } from "@/lib/api";

interface UrlMetadata {
  title: string | null;
  description: string | null;
  favicon: string | null;
  website_name: string | null;
  website_image: string | null;
  url: string;
}

interface UrlMetadataError {
  message: string;
  code?: number;
}

const isEmail = (str: string) => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(str);

/**
 * Custom hook to fetch URL metadata with React Query optimization
 * Features:
 * - Automatic caching with 5-minute stale time
 * - Deduplication of identical requests
 * - Background refetching for fresh data
 * - Error handling with retry logic
 * - Conditional fetching based on URL validity
 */
export const useUrlMetadata = (url: string | undefined | null) => {
  const isValidUrl = url && !isEmail(url) && !url.startsWith("mailto:");

  const result = useQuery<UrlMetadata, UrlMetadataError>({
    queryKey: ["url-metadata", url],
    queryFn: async () => {
      if (!url) {
        throw new Error("URL is required");
      }

      const response = await api.post("/fetch-url-metadata", { url });
      return response.data;
    },
    staleTime: 5 * 60 * 1000, // 5 minutes - metadata rarely changes
    gcTime: 30 * 60 * 1000, // 30 minutes - keep in cache for longer
    retry: (failureCount, error) => {
      if (
        error &&
        "code" in error &&
        error.code &&
        error.code >= 400 &&
        error.code < 500
      ) {
        return false;
      }
      return failureCount < 2;
    },
    retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 5000),
    refetchOnWindowFocus: false,
    refetchOnMount: false,
    refetchOnReconnect: "always",
  });

  // Return early state for invalid URLs, but after calling useQuery
  if (!isValidUrl) {
    return { data: null, isLoading: false, isError: false, error: null };
  }

  return result;
};

/**
 * Hook to prefetch URL metadata for better UX
 * Useful for prefetching when user hovers over links
 */
export const usePrefetchUrlMetadata = () => {
  const queryClient = useQueryClient();

  return (url: string) => {
    if (!url) return;

    queryClient.prefetchQuery({
      queryKey: ["url-metadata", url],
      queryFn: async () => {
        const response = await api.post("/fetch-url-metadata", { url });
        return response.data;
      },
      staleTime: 30 * 24 * 60 * 60 * 1000, // 1 month
    });
  };
};
