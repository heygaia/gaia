import React from "react";

import { Gmail } from "@/components";
import EmailListCard from "@/features/mail/components/EmailListCard";
import BaseCardView from "@/features/shared/components/BaseCardView";
import { EmailData, EmailFetchData } from "@/types/features/mailTypes";

interface UnreadEmailsViewProps {
  emails?: EmailData[];
  isLoading: boolean;
  error?: Error | null;
}

const UnreadEmailsView: React.FC<UnreadEmailsViewProps> = ({
  emails,
  isLoading,
  error,
}) => {
  // Convert EmailData to EmailFetchData format expected by EmailListCard
  const formattedEmails: EmailFetchData[] =
    emails?.map((email: EmailData) => ({
      from: email.from || "",
      subject: email.subject || "No Subject",
      time: email.time || "",
      thread_id: email.threadId || email.id,
    })) || [];

  const isEmpty = !formattedEmails || formattedEmails.length === 0;

  return (
    <BaseCardView
      title="Unread emails"
      icon={<Gmail width={24} height={24} className="text-zinc-500" />}
      isLoading={isLoading}
      error={error?.message}
      isEmpty={isEmpty}
      emptyMessage="No unread emails"
      errorMessage="Failed to load unread emails"
    >
      <EmailListCard
        emails={formattedEmails}
        backgroundColor="bg-[#141414]"
        showTitle={false}
        maxHeight=""
      />
    </BaseCardView>
  );
};

export default UnreadEmailsView;
