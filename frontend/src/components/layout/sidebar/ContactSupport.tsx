"use client";

import { Button } from "@heroui/button";
import { useDisclosure } from "@heroui/modal";
import { Tooltip } from "@heroui/react";

import { HealtcareIcon } from "@/components/shared/icons";
import { ContactSupportModal } from "@/features/support";

export default function ContactSupport() {
  const { isOpen, onOpen, onOpenChange } = useDisclosure();

  return (
    <>
      <div className="flex w-full justify-center">
        <Tooltip content="Need support or want a new feature? Talk to us!">
          <Button
            variant="flat"
            className="flex h-fit w-full justify-center gap-2 pl-3"
            radius="sm"
            onPress={onOpen}
          >
            <HealtcareIcon width={23} height={23} color={undefined} />
            <div className="w-full py-2 text-left text-sm font-light text-wrap">
              Need Support?
            </div>
          </Button>
        </Tooltip>
      </div>

      <ContactSupportModal isOpen={isOpen} onOpenChange={onOpenChange} />
    </>
  );
}
