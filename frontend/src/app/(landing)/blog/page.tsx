"use client";

import { Button } from "@heroui/button";
import { useEffect, useState } from "react";

import { blogApi, type BlogPost } from "@/features/blog/api/blogApi";
import { BlogCard } from "@/features/blog/components/BlogCard";
import { BlogHeader } from "@/features/blog/components/BlogHeader";
import { BlogListItem } from "@/features/blog/components/BlogListItem";

interface Blog {
  slug: string;
  title: string;
  category: string;
  date: string;
  image: string;
  authors: Array<{
    name: string;
    role: string;
    avatar: string;
    linkedin?: string;
    twitter?: string;
  }>;
}

export default function BlogList() {
  const [blogs, setBlogs] = useState<BlogPost[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchBlogs = async () => {
      try {
        setLoading(true);
        const blogsData = await blogApi.getBlogs(false); // Don't include content for list view - better performance
        setBlogs(blogsData);
        setError(null);
      } catch (err) {
        console.error("Error fetching blogs:", err);
        setError(err instanceof Error ? err.message : "Failed to fetch blogs");
      } finally {
        setLoading(false);
      }
    };

    fetchBlogs();
  }, []);

  // Convert BlogPost to Blog format for compatibility
  const displayBlogs: Blog[] = blogs.map((blog) => ({
    slug: blog.slug,
    title: blog.title,
    category: blog.category || "Uncategorized",
    date: blog.date,
    image: blog.image || "/images/logos/logo_glass.webp",
    authors:
      blog.author_details?.map((author) => ({
        name: author.name,
        role: author.role,
        avatar:
          author.avatar ||
          `https://api.dicebear.com/9.x/notionists/svg?seed=${author.name}`,
        linkedin: author.linkedin,
        twitter: author.twitter,
      })) ||
      blog.authors.map((name) => ({
        name,
        role: "Author",
        avatar: `https://api.dicebear.com/9.x/notionists/svg?seed=${name}`,
      })),
  }));

  const latestPosts = displayBlogs.slice(0, 5);
  const remainingPosts = displayBlogs.slice(5);

  if (loading) {
    return (
      <div className="flex min-h-screen w-screen justify-center px-6 pt-28">
        <div className="w-full max-w-(--breakpoint-lg)">
          <BlogHeader />
          <div className="flex flex-col items-center justify-center py-20">
            <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent"></div>
            <span className="mt-4 text-foreground-500">
              Loading blog posts...
            </span>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex min-h-screen w-screen justify-center px-6 pt-28">
        <div className="w-full max-w-(--breakpoint-lg)">
          <BlogHeader />
          <div className="flex flex-col items-center justify-center py-20">
            <span className="text-danger">Error loading blog posts</span>
            <span className="mt-2 text-sm text-foreground-500">{error}</span>
            <Button onPress={() => window.location.reload()}>Retry</Button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen w-screen justify-center px-6 pt-28">
      <div className="w-full max-w-(--breakpoint-lg)">
        <BlogHeader />

        {/* Latest Posts Grid */}
        {latestPosts.length > 0 && (
          <div className="mb-12 px-3 sm:px-6">
            <div className="mb-6 grid gap-6">
              {/* First row - 2 posts */}
              <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
                {latestPosts.slice(0, 2).map((blog) => (
                  <BlogCard key={blog.slug} blog={blog} variant="large" />
                ))}
              </div>

              {/* Second row - 3 posts */}
              {latestPosts.length > 2 && (
                <div className="grid grid-cols-1 gap-6 md:grid-cols-3">
                  {latestPosts.slice(2, 5).map((blog) => (
                    <BlogCard key={blog.slug} blog={blog} variant="small" />
                  ))}
                </div>
              )}
            </div>
          </div>
        )}

        {/* More News Section */}
        {remainingPosts.length > 0 && (
          <div className="dark">
            <div className="my-7 space-y-2 px-6">
              <div className="text-sm font-medium text-foreground-300">
                More News
              </div>
              <div className="h-px w-full bg-foreground-300"></div>
            </div>
            {remainingPosts.map((blog) => (
              <BlogListItem key={blog.slug} blog={blog} />
            ))}
          </div>
        )}

        {displayBlogs.length === 0 && (
          <p className="flex h-full items-center justify-center text-center text-zinc-400">
            No posts available.
          </p>
        )}
      </div>
    </div>
  );
}
