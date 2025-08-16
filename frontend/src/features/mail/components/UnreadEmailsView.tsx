import { Spinner } from "@heroui/react";
import React from "react";

import { Gmail } from "@/components";
import EmailListCard from "@/features/mail/components/EmailListCard";
import { useUnreadEmails } from "@/features/mail/hooks/useUnreadEmails";
import { EmailFetchData } from "@/types/features/mailTypes";

const UnreadEmailsView: React.FC = () => {
  const { data: unreadEmails, isLoading, error } = useUnreadEmails(10);

  if (isLoading) {
    return (
      <div className="flex h-full w-full items-center justify-center">
        <div className="flex flex-col items-center gap-3">
          <Spinner size="sm" color="primary" />
          <span className="text-sm text-foreground/60">
            Loading unread emails...
          </span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex h-full w-full items-center justify-center">
        <div className="text-center">
          <Gmail width={32} height={32} className="mx-auto mb-2 opacity-50" />
          <p className="text-sm text-foreground/60">
            Failed to load unread emails
          </p>
        </div>
      </div>
    );
  }

  // Convert EmailData to EmailFetchData format expected by EmailListCard
  const formattedEmails: EmailFetchData[] =
    unreadEmails?.map((email) => ({
      from: email.from || "",
      subject: email.subject || "No Subject",
      time: email.time || "",
      thread_id: email.threadId || email.id,
    })) || [];

  if (!formattedEmails || formattedEmails.length === 0) {
    return (
      <div className="flex h-full w-full flex-col">
        {/* Sticky Header */}
        <div className="px-4 py-3">
          <div className="flex items-center gap-2">
            <Gmail width={24} height={24} className="text-zinc-500" />
            <h3 className="font-medium text-white">Unread emails</h3>
          </div>
        </div>

        {/* Empty State */}
        <div className="mx-4 mb-4 flex flex-1 items-center justify-center rounded-2xl bg-[#141414]">
          <div className="text-center">
            <Gmail width={32} height={32} className="mx-auto mb-2 opacity-50" />
            <p className="text-sm text-foreground/60">No unread emails</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-full w-full flex-col">
      <div className="px-4 py-3">
        <div className="flex items-center gap-2">
          <Gmail width={24} height={24} className="text-zinc-500" />
          <h3 className="font-medium text-white">Unread emails</h3>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto rounded-2xl bg-[#141414] px-4 pb-4">
        <EmailListCard
          emails={formattedEmails}
          backgroundColor="bg-[#141414]"
          showTitle={false}
          maxHeight=""
        />
      </div>
    </div>
  );
};

export default UnreadEmailsView;
