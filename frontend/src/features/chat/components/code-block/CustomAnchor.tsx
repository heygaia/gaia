import { ReactNode } from "react";

const CustomAnchor = ({
  href,
  children,
}: {
  href: string | undefined;
  children: ReactNode | string | null;
}) => {
  if (!href) return null;

  return (
    <a
      href={href}
      className="cursor-pointer rounded-sm bg-primary/20 px-1 text-sm font-medium text-primary transition-all hover:text-white hover:underline"
      rel="noopener noreferrer"
      target="_blank"
    >
      {children}
    </a>
  );
};

export default CustomAnchor;
