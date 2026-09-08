// @vitest-environment jsdom
/**
 * The persisted `["current-user"]` entry paints the shell on reload, but it is
 * last session's answer. The onboarding wizard reconciles its browser draft
 * against the account, so it must wait for a fetch from this page session;
 * acting on the replayed entry re-completed onboarding after a server-side
 * reset (found on the dev reset script's live drive).
 */
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { renderHook } from "@testing-library/react";
import type { ReactNode } from "react";
import { describe, expect, it } from "vitest";

import type { UserInfo } from "@/features/auth/api/authApi";
import {
  CURRENT_USER_QUERY_KEY,
  isFetchedThisSession,
  useCurrentUserIsFresh,
} from "@/features/auth/hooks/useCurrentUser";

const USER: UserInfo = {
  user_id: "user1",
  name: "Alice",
  email: "alice@example.com",
  picture: "",
};

const PAGE_LOADED_AT = 1_000_000;

describe("isFetchedThisSession", () => {
  it("treats a timestamp older than the page as a replayed cache entry", () => {
    expect(isFetchedThisSession(PAGE_LOADED_AT - 1, PAGE_LOADED_AT)).toBe(
      false,
    );
  });

  it("treats a timestamp from this session as fresh", () => {
    expect(isFetchedThisSession(PAGE_LOADED_AT, PAGE_LOADED_AT)).toBe(true);
    expect(isFetchedThisSession(PAGE_LOADED_AT + 5, PAGE_LOADED_AT)).toBe(true);
  });
});

describe("useCurrentUserIsFresh", () => {
  const render = (updatedAt: number) => {
    const client = new QueryClient();
    client.setQueryData(CURRENT_USER_QUERY_KEY, USER, { updatedAt });
    const wrapper = ({ children }: { children: ReactNode }) => (
      <QueryClientProvider client={client}>{children}</QueryClientProvider>
    );
    return renderHook(() => useCurrentUserIsFresh(), { wrapper }).result
      .current;
  };

  it("is false while the only user is a replay from before this page loaded", () => {
    expect(render(performance.timeOrigin - 60_000)).toBe(false);
  });

  it("is true once the user was fetched in this session", () => {
    expect(render(Date.now())).toBe(true);
  });
});
