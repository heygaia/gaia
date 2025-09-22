import { Metadata } from "next";

import { BlogPost } from "@/features/blog/api/blogApi";

/**
 * Extracts description from markdown content for meta descriptions
 */
export function extractDescription(
  markdown: string,
  maxLength: number = 160,
): string {
  if (!markdown) return "";

  // Remove markdown syntax
  const text = markdown
    .replace(/#{1,6}\s+/g, "")
    .replace(/[*_]{1,2}([^*_]+)[*_]{1,2}/g, "$1")
    .replace(/\[([^\]]+)\]\([^)]+\)/g, "$1")
    .replace(/`([^`]+)`/g, "$1")
    .replace(/```[\s\S]*?```/g, "")
    .replace(/\s+/g, " ")
    .trim();

  if (text.length <= maxLength) return text;

  const truncated = text.substring(0, maxLength);
  const lastSpace = truncated.lastIndexOf(" ");
  return lastSpace > 100
    ? truncated.substring(0, lastSpace) + "..."
    : truncated + "...";
}

/**
 * Generates metadata for a blog post
 */
export function generateBlogMetadata(blog: BlogPost): Metadata {
  const description = extractDescription(blog.content);
  const canonicalUrl = `https://heygaia.io/blog/${blog.slug}`;
  const imageUrl = blog.image || "/landing/screenshot.webp";

  return {
    title: blog.title,
    description,
    authors:
      blog.author_details?.map((author) => ({ name: author.name })) ||
      blog.authors.map((name) => ({ name })),

    openGraph: {
      title: blog.title,
      description,
      url: canonicalUrl,
      siteName: "GAIA - AI Personal Assistant",
      images: [{ url: imageUrl, width: 1200, height: 630, alt: blog.title }],
      type: "article",
      publishedTime: blog.date,
      authors:
        blog.author_details?.map((author) => author.name) || blog.authors,
      section: blog.category,
    },

    twitter: {
      card: "summary_large_image",
      title: blog.title,
      description,
      images: [imageUrl],
      site: "@heygaia",
    },

    alternates: { canonical: canonicalUrl },
    robots: { index: true, follow: true },
  };
}

/**
 * Generates JSON-LD structured data for a blog post
 */
export function generateBlogStructuredData(blog: BlogPost) {
  return {
    "@context": "https://schema.org",
    "@type": "BlogPosting",
    headline: blog.title,
    description: extractDescription(blog.content),
    image: blog.image || "/landing/screenshot.webp",
    author:
      blog.author_details?.map((author) => ({
        "@type": "Person",
        name: author.name,
        jobTitle: author.role,
      })) || blog.authors.map((name) => ({ "@type": "Person", name })),
    publisher: {
      "@type": "Organization",
      name: "GAIA",
      logo: { "@type": "ImageObject", url: "https://heygaia.io/logo.png" },
    },
    datePublished: blog.date,
    url: `https://heygaia.io/blog/${blog.slug}`,
    articleSection: blog.category,
    inLanguage: "en-US",
  };
}
