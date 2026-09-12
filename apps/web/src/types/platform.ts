import type { Schema } from "@shared/api/generated";

/** The map `GET /platform-links` returns: platform id to its link. */
export type PlatformLinks =
  Schema<"GetPlatformLinksResponse">["platform_links"];
