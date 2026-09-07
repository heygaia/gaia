import { QueryClient } from "@tanstack/react-query";

/**
 * The browser's single QueryClient.
 *
 * `QueryProvider` renders this instance, so non-React code (module-level
 * helpers that need cached server data, e.g. `getUserHomeTimezone`) can read
 * the same cache the components read instead of keeping a second copy of the
 * data in a store.
 *
 * On the server every render gets a fresh client — a module-level singleton
 * there would leak one request's data into the next.
 */
const queryClientOptions = {
  defaultOptions: {
    queries: {
      // With SSR, we usually want to set some default staleTime
      // above 0 to avoid refetching immediately on the client
      staleTime: 60 * 1000, // 1 minute (default for most queries)
      retry: 2,
      refetchOnWindowFocus: false,
    },
  },
};

let browserQueryClient: QueryClient | undefined;

export const getQueryClient = (): QueryClient => {
  if (typeof window === "undefined") return new QueryClient(queryClientOptions);
  browserQueryClient ??= new QueryClient(queryClientOptions);
  return browserQueryClient;
};
