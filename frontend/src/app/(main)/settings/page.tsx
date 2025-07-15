"use client";

import { useRouter,useSearchParams } from "next/navigation";
import { useEffect, useState } from "react";

import AccountSettings from "@/components/layout/sidebar/settings/AccountSettings";
import LogoutModal from "@/components/layout/sidebar/settings/LogoutModal";
import MemorySettings from "@/components/layout/sidebar/settings/MemorySettings";
import PreferencesSettings from "@/components/layout/sidebar/settings/PreferencesSettings";
import { ModalAction } from "@/components/layout/sidebar/settings/SettingsMenu";
import { IntegrationsSettings } from "@/features/integrations/components/IntegrationsSettings";
import { SubscriptionSettings } from "@/features/settings/components/SubscriptionSettings";
import UsageSettings from "@/features/settings/components/UsageSettings";

export default function SettingsPage() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const section = searchParams.get("section");
  const [modalAction, setModalAction] = useState<ModalAction | null>(null);

  // Redirect to /settings?section=account if no section is specified
  useEffect(() => {
    if (!section) {
      router.replace("?section=account");
    }
  }, [section, router]);

  const renderContent = () => {
    switch (section) {
      case "account":
        return <AccountSettings setModalAction={setModalAction} />;
      case "subscription":
        return <SubscriptionSettings />;
      case "usage":
        return <UsageSettings />;
      case "preferences":
        return <PreferencesSettings setModalAction={setModalAction} />;
      case "memory":
        return <MemorySettings />;
      case "integrations":
        return <IntegrationsSettings />;
      default:
        return <AccountSettings setModalAction={setModalAction} />;
    }
  };

  return (
    <>
      <div className="flex h-full w-full flex-col">
        <div className="flex-1 overflow-y-auto">
          <div className="flex w-full justify-center p-6">
            <div className="w-full max-w-2xl">{renderContent()}</div>
          </div>
        </div>
      </div>

      <LogoutModal modalAction={modalAction} setModalAction={setModalAction} />
    </>
  );
}
