import Link from "next/link";

import { type Author } from "@/types";

import { AuthorTooltip } from "./AuthorTooltip";

export interface Blog {
  slug: string;
  title: string;
  category: string;
  date: string;
  authors: Author[];
}

interface BlogListItemProps {
  blog: Blog;
}

export function BlogListItem({ blog }: BlogListItemProps) {
  return (
    <div>
      <Link href={`/blog/${blog.slug}`} className="block">
        <div className="grid grid-cols-[minmax(0,4fr)_minmax(0,1.5fr)_minmax(0,1fr)_minmax(0,0.7fr)] items-center rounded-lg px-6 py-4 transition-all hover:bg-zinc-800">
          <div className="truncate text-sm">{blog.title}</div>
          <div className="text-sm text-foreground-400">{blog.category}</div>
          <div className="text-sm text-foreground-400">{blog.date}</div>
          <div className="flex items-center -space-x-1">
            {blog.authors.map((author) => (
              <AuthorTooltip
                key={author.name}
                author={author}
                avatarClassName="h-6 w-6 cursor-help"
              />
            ))}
          </div>
        </div>
      </Link>
    </div>
  );
}
