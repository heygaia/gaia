"use client";

import { Button } from "@heroui/button";
import { Link } from "@heroui/link";
import {
  Modal,
  ModalBody,
  ModalContent,
  ModalFooter,
  ModalHeader,
} from "@heroui/modal";
import { Skeleton } from "@heroui/skeleton";
import { ArcBrowserIcon, ChromeIcon, EdgeStyleIcon, GlobalIcon } from "@icons";
import { type ComponentType, useEffect, useState } from "react";
import CopyButton from "@/components/ui/CopyButton";
import {
  type ConnectableBrowser,
  GAIA_CONNECT_README_URL,
  SAVED_LOGIN_TTL_DAYS,
} from "../constants";
import { useImportToken } from "../hooks/useImportToken";
import {
  buildConnectCommand,
  connectApiOrigin,
  formatCountdown,
} from "../utils";

/** Countdown turns amber inside the last minute so the user acts before it dies. */
const EXPIRY_WARNING_SECONDS = 60;

interface BrowserOption {
  label: string;
  value: ConnectableBrowser | null;
  icon: ComponentType<{ className?: string }>;
}

const BROWSER_OPTIONS: readonly BrowserOption[] = [
  { label: "Arc", value: "Arc", icon: ArcBrowserIcon },
  { label: "Chrome", value: "Chrome", icon: ChromeIcon },
  { label: "Edge", value: "Edge", icon: EdgeStyleIcon },
  { label: "Other", value: null, icon: GlobalIcon },
];

const WHAT_HAPPENS: readonly { heading: string; body: string }[] = [
  {
    heading: "Your browser asks once",
    body: "The tool reads your browser's own encrypted cookies. macOS asks for permission one time; that prompt is your consent.",
  },
  {
    heading: "You choose the sites",
    body: "Pick exactly which sites to sync. Only their sign-in sessions are uploaded, never your passwords.",
  },
  {
    heading: "Encrypted, and yours to forget",
    body: `Saved sites are stored encrypted and expire ${SAVED_LOGIN_TTL_DAYS} days after last use. Forget any site from this page whenever you like.`,
  },
];

function BrowserPicker({
  value,
  onChange,
}: {
  value: ConnectableBrowser | null;
  onChange: (browser: ConnectableBrowser | null) => void;
}) {
  return (
    <div className="flex flex-wrap gap-2">
      {BROWSER_OPTIONS.map(({ label, value: option, icon: Icon }) => {
        const selected = option === value;
        return (
          <Button
            key={label}
            size="sm"
            radius="full"
            variant={selected ? "solid" : "flat"}
            color={selected ? "primary" : "default"}
            startContent={<Icon className="size-4" />}
            onPress={() => onChange(option)}
          >
            {label}
          </Button>
        );
      })}
    </div>
  );
}

function CommandBlock({ command }: { command: string }) {
  return (
    <div className="flex items-center gap-3 rounded-2xl bg-zinc-900 py-2 pr-2 pl-4">
      <code className="min-w-0 flex-1 break-all text-primary text-sm">
        {command}
      </code>
      <CopyButton textToCopy={command} />
    </div>
  );
}

/**
 * Rendered inside `<ModalContent>`, so it unmounts when the modal closes: a
 * fresh code is minted on every open and nothing needs resetting.
 */
function ConnectBrowserBody({ onClose }: { onClose: () => void }) {
  const { token, secondsLeft, isExpired, isMinting, error, mint } =
    useImportToken();
  const [browser, setBrowser] = useState<ConnectableBrowser | null>(null);

  useEffect(() => {
    mint();
  }, [mint]);

  const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL;
  const command =
    token && apiBaseUrl
      ? buildConnectCommand({
          apiOrigin: connectApiOrigin(apiBaseUrl),
          token,
          browser,
        })
      : null;

  return (
    <>
      <ModalHeader>Connect your browser</ModalHeader>
      <ModalBody className="gap-5">
        <p className="text-sm text-zinc-400">
          Bring over the sites you're already signed into. GAIA's browser then
          starts each task signed in, instead of asking you to log in again.
        </p>

        <section className="flex flex-col gap-2">
          <h4 className="font-medium text-sm text-zinc-200">Which browser?</h4>
          <BrowserPicker value={browser} onChange={setBrowser} />
        </section>

        <section className="flex flex-col gap-2">
          <h4 className="font-medium text-sm text-zinc-200">
            Run this in Terminal
          </h4>
          {isMinting || (!command && !error && !isExpired) ? (
            <Skeleton className="h-10 w-full rounded-2xl" />
          ) : error ? (
            <div className="flex items-center justify-between gap-3 rounded-2xl bg-zinc-800/40 p-3 text-sm text-zinc-400">
              <span>Couldn't get a code.</span>
              <Button size="sm" variant="flat" onPress={mint}>
                Try again
              </Button>
            </div>
          ) : isExpired || !command ? (
            <div className="flex items-center justify-between gap-3 rounded-2xl bg-zinc-800/40 p-3 text-sm text-zinc-400">
              <span>This code expired.</span>
              <Button size="sm" color="primary" onPress={mint}>
                Get a new code
              </Button>
            </div>
          ) : (
            <>
              <CommandBlock command={command} />
              <p
                className={`text-xs ${secondsLeft <= EXPIRY_WARNING_SECONDS ? "text-amber-400/80" : "text-zinc-500"}`}
              >
                It'll ask which sites to sync, then upload only those. Code
                expires in {formatCountdown(secondsLeft)}.
              </p>
            </>
          )}
        </section>

        <section className="flex flex-col gap-3">
          <h4 className="font-medium text-sm text-zinc-200">What happens</h4>
          <ol className="flex flex-col gap-3">
            {WHAT_HAPPENS.map(({ heading, body }, index) => (
              <li key={heading} className="flex gap-3">
                <span className="flex size-6 shrink-0 items-center justify-center rounded-full bg-zinc-800 font-medium text-xs text-zinc-300">
                  {index + 1}
                </span>
                <div className="min-w-0">
                  <p className="text-sm text-zinc-200">{heading}</p>
                  <p className="mt-0.5 text-xs text-zinc-500 leading-relaxed">
                    {body}
                  </p>
                </div>
              </li>
            ))}
          </ol>
        </section>

        <p className="text-xs text-zinc-500">
          Works on macOS with Arc, Chrome, Edge, Brave, and other Chromium
          browsers. Windows and Linux are coming. Don't have gaia-connect yet?{" "}
          <Link
            href={GAIA_CONNECT_README_URL}
            isExternal
            size="sm"
            className="text-xs"
          >
            Get it here
          </Link>
        </p>
      </ModalBody>
      <ModalFooter>
        <Button color="primary" size="sm" onPress={onClose}>
          Done
        </Button>
      </ModalFooter>
    </>
  );
}

interface ConnectBrowserModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export function ConnectBrowserModal({
  isOpen,
  onClose,
}: ConnectBrowserModalProps) {
  return (
    <Modal isOpen={isOpen} onClose={onClose} size="lg" scrollBehavior="inside">
      <ModalContent>
        <ConnectBrowserBody onClose={onClose} />
      </ModalContent>
    </Modal>
  );
}
