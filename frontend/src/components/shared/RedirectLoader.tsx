"use client";

import Image from "next/image";
import { useRouter } from "next/navigation";
import { useEffect } from "react";

interface RedirectLoaderProps {
  url: string;
  external?: boolean;
  replace?: boolean;
}

export function RedirectLoader({ url, replace = false }: RedirectLoaderProps) {
  const router = useRouter();

  useEffect(() => {
    const navigator = replace ? router.replace : router.push;
    navigator(url);
  }, [url, router, replace]);

  return (
    <div className="inset-0 flex h-full flex-1 flex-col items-center justify-center bg-background">
      <div className="mb-6 animate-spin">
        <Image
          src="/images/logos/logo.webp"
          alt="GAIA"
          width={100}
          height={100}
          priority
        />
      </div>
      <div className="text-lg font-medium text-foreground">
        Redirecting you...
      </div>
    </div>
  );
}
