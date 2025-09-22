import { Avatar } from "@heroui/avatar";
import { Tooltip } from "@heroui/tooltip";

import { LinkedinIcon, TwitterIcon } from "@/components/shared/icons";

export interface Author {
  name: string;
  avatar: string;
  role: string;
  linkedin?: string;
  twitter?: string;
}

interface AuthorTooltipProps {
  author: Author;
  avatarSize?: "sm" | "md" | "lg";
  avatarClassName?: string;
}

export function AuthorTooltip({
  author,
  avatarSize = "sm",
  avatarClassName = "h-8 w-8 cursor-help border-2 border-zinc-700",
}: AuthorTooltipProps) {
  return (
    <Tooltip
      content={
        <div className="flex flex-row items-center gap-3 p-2">
          <Avatar
            src={author.avatar}
            size="sm"
            className="h-8 w-8"
            name={author.name}
          />
          <div className="flex flex-col">
            <span className="text-medium">{author.name}</span>
            <span className="text-xs text-foreground-500">{author.role}</span>
          </div>
          <div className="mt-1 ml-6 flex gap-2">
            {author.linkedin && (
              <a
                href={author.linkedin}
                target="_blank"
                rel="noopener noreferrer"
              >
                <LinkedinIcon width={20} height={20} />
              </a>
            )}
            {author.twitter && (
              <a
                href={author.twitter}
                target="_blank"
                rel="noopener noreferrer"
              >
                <TwitterIcon width={20} height={20} />
              </a>
            )}
          </div>
        </div>
      }
      classNames={{ content: "text-nowrap" }}
    >
      <Avatar
        src={author.avatar}
        size={avatarSize}
        className={avatarClassName}
        name={author.name}
      />
    </Tooltip>
  );
}
