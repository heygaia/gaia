import {
  DiscordIcon,
  Github,
  LinkedinIcon,
  Mail01Icon,
  TwitterIcon,
  WhatsappIcon,
  YoutubeIcon,
} from "@/components/shared/icons";
import { HandMetal, LockIcon } from "lucide-react";

export default function ContactSidebar() {
  return (
    <div className="grid gap-10">
      <section aria-labelledby="email-heading">
        <h3
          id="email-heading"
          className="mb-3 text-base font-semibold tracking-tight"
        >
          Get in Touch
        </h3>
        <a
          href="mailto:contact@heygaia.io"
          className="text-muted-foreground inline-flex items-center gap-2 text-foreground-500 hover:underline"
        >
          <Mail01Icon className="size-5" aria-hidden="true" color={undefined} />
          contact@heygaia.io
        </a>
        <a
          href="mailto:ceo@heygaia.io"
          className="text-muted-foreground inline-flex items-center gap-2 text-foreground-500 hover:underline"
        >
          <HandMetal className="size-5" aria-hidden="true" color={undefined} />
          ceo@heygaia.io
        </a>
        <a
          href="mailto:ceo@heygaia.io"
          className="text-muted-foreground inline-flex items-center gap-2 text-foreground-500 hover:underline"
        >
          <LockIcon className="size-5" aria-hidden="true" color={undefined} />
          security@heygaia.io
        </a>
      </section>

      <section aria-labelledby="follow-heading">
        <h3
          id="follow-heading"
          className="text-base font-semibold tracking-tight"
        >
          Socials
        </h3>
        <div className="mt-3 flex items-center gap-2 text-foreground-500">
          <a
            aria-label="Discord"
            href="https://discord.heygaia.io"
            target="_blank"
            rel="noopener noreferrer"
            className="hover:text-foreground"
          >
            <DiscordIcon className="size-5" />
          </a>
          <a
            aria-label="Twitter"
            href="https://x.com/_heygaia"
            target="_blank"
            rel="noopener noreferrer"
            className="hover:text-foreground"
          >
            <TwitterIcon className="size-5" />
          </a>
          <a
            aria-label="GitHub"
            href="https://github.com/heygaia"
            target="_blank"
            rel="noopener noreferrer"
            className="hover:text-foreground"
          >
            <Github className="size-5" />
          </a>
          <a
            aria-label="WhatsApp"
            href="https://whatsapp.heygaia.io"
            target="_blank"
            rel="noopener noreferrer"
            className="hover:text-foreground"
          >
            <WhatsappIcon className="size-5" />
          </a>
          <a
            aria-label="YouTube"
            href="https://youtube.com/@heygaia_io"
            target="_blank"
            rel="noopener noreferrer"
            className="hover:text-foreground"
          >
            <YoutubeIcon className="size-5" />
          </a>
          <a
            aria-label="LinkedIn"
            href="https://www.linkedin.com/company/heygaia"
            target="_blank"
            rel="noopener noreferrer"
            className="hover:text-foreground"
          >
            <LinkedinIcon className="size-5" />
          </a>
        </div>
      </section>
    </div>
  );
}
