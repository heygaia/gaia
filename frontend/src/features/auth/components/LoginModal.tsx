"use client";

import { Modal, ModalBody, ModalContent } from "@heroui/modal";
import Link from "next/link";
import { usePathname } from "next/navigation";

import { GoogleColouredIcon } from "@/components/shared/icons";
import { handleGoogleLogin } from "@/features/auth/hooks/handleGoogleLogin";
import {
  useLoginModal,
  useLoginModalActions,
} from "@/features/auth/hooks/useLoginModal";

import { Button } from "../../../components/ui/shadcn/button";

export default function LoginModal() {
  const isOpen = useLoginModal();
  const { setLoginModalOpen } = useLoginModalActions();
  const pathname = usePathname();

  // Prevent rendering on /login or /signup pages
  if (pathname === "/login" || pathname === "/signup") return null;

  return (
    <Modal
      isOpen={isOpen}
      onOpenChange={(v) => setLoginModalOpen(v)}
      isDismissable={false}
      isKeyboardDismissDisabled
      hideCloseButton
    >
      <ModalContent className="p-7">
        <ModalBody>
          <div className="mb-3 space-y-2 text-center">
            <div className="text-5xl font-medium">Login</div>
            <div className="text-md text-foreground-600">
              Please login to continue your journey with GAIA.
            </div>
          </div>
          <Button
            size="lg"
            className={`text-md gap-2 rounded-full bg-zinc-800 px-4 text-foreground hover:bg-zinc-800`}
            onClick={handleGoogleLogin}
          >
            <GoogleColouredIcon />
            Sign in with Google
          </Button>
          <Link
            href="/signup"
            className="text-md w-full gap-2 rounded-full px-4 text-center font-normal text-primary"
            onClick={() => setLoginModalOpen(false)}
          >
            New to GAIA? Create an Account
          </Link>
        </ModalBody>
      </ModalContent>
    </Modal>
  );
}
