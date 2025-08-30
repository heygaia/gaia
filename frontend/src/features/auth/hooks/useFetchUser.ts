"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { useCallback, useEffect } from "react";

import { authApi } from "@/features/auth/api/authApi";
import { useUserActions } from "@/features/auth/hooks/useUser";

export const authPages = ["/login", "/signup"];
export const publicPages = [...authPages, "/terms", "/privacy", "/contact"];

const useFetchUser = () => {
  const { setUser, clearUser } = useUserActions();
  const searchParams = useSearchParams();
  const router = useRouter();

  const fetchUserInfo = useCallback(async () => {
    try {
      const accessToken = searchParams.get("access_token");
      const refreshToken = searchParams.get("refresh_token");
      const currentPath = window.location.pathname;

      const data = await authApi.fetchUserInfo();

      setUser({
        name: data?.name,
        email: data?.email,
        profilePicture: data?.picture,
        timezone: data?.timezone,
        onboarding: data?.onboarding,
      });

      // Check if onboarding is needed and prevent navigation loops
      if (accessToken && refreshToken) {
        const needsOnboarding = !data?.onboarding?.completed;

        if (needsOnboarding && currentPath !== "/onboarding") {
          router.push("/onboarding");
        } else if (
          !needsOnboarding &&
          (currentPath === "/onboarding" || publicPages.includes(currentPath))
        ) {
          router.push("/c");
        }
      }
    } catch (e: unknown) {
      console.error("Error fetching user info:", e);
      clearUser();
    }
  }, [searchParams, setUser, clearUser, router]);

  useEffect(() => {
    fetchUserInfo();
  }, [fetchUserInfo]);

  return { fetchUserInfo };
};

export default useFetchUser;
