"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { useCallback, useEffect, useRef } from "react";

import { authApi } from "@/features/auth/api/authApi";
import { useUserActions } from "@/features/auth/hooks/useUser";

export const authPages = ["/login", "/signup", "/signup"];
export const publicPages = [...authPages, "/terms", "/privacy", "/contact"];

const useFetchUser = () => {
  const { setUser, clearUser } = useUserActions();
  const searchParams = useSearchParams();
  const router = useRouter();
  const navigationHandledRef = useRef<boolean>(false);

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
        onboarding: data?.onboarding,
      });

      // Only run navigation logic if we have OAuth tokens (i.e., just logged in)
      // and navigation hasn't been handled yet for this session
      if (accessToken && refreshToken && !navigationHandledRef.current) {
        navigationHandledRef.current = true;
        const needsOnboarding = !data?.onboarding?.completed;

        if (needsOnboarding && currentPath !== "/onboarding")
          router.push("/onboarding");
        else if (
          !needsOnboarding &&
          (currentPath === "/onboarding" || publicPages.includes(currentPath))
        )
          router.replace("/c");
      }
    } catch (e: unknown) {
      console.error("Error fetching user info:", e);
      clearUser();
      navigationHandledRef.current = false;
    }
  }, [searchParams, setUser, clearUser, router]);

  useEffect(() => {
    fetchUserInfo();
  }, [fetchUserInfo]);

  return { fetchUserInfo };
};

export default useFetchUser;
