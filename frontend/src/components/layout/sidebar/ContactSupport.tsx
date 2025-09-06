"use client";

import { Button } from "@heroui/button";
import { useDisclosure } from "@heroui/react";
import { Tooltip } from "@heroui/tooltip";

import { HelpCircleIcon } from "@/components/shared/icons";
import { ContactSupportModal } from "@/features/support";

export default function ContactSupport() {
  const { isOpen, onOpen, onOpenChange } = useDisclosure();

  return (
    <>
      <div className="flex w-full justify-center">
        <Tooltip content="Contact Support or Request a Feature">
          <Button
            variant="flat"
            className="mx-0.5 flex h-fit w-full gap-2 pl-3"
            onPress={onOpen}
          >
            <HelpCircleIcon width={23} height={23} color={undefined} />
            <div className="w-full py-2 text-left text-sm font-light text-wrap">
              Need help or want a feature?
            </div>
          </Button>
        </Tooltip>
      </div>

      <ContactSupportModal isOpen={isOpen} onOpenChange={onOpenChange} />
    </>
  );
}
