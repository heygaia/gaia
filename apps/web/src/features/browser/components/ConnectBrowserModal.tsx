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
import { type ComponentType, type ReactNode, useEffect, useState } from "react";
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

const FACTS: readonly string[] = [
  "Cookies only, never passwords. macOS asks permission once.",
  "You pick which sites to sync.",
  `Encrypted. Expires ${SAVED_LOGIN_TTL_DAYS} days after last use; forget any site here.`,
];

/** A tonal card: zinc-800 on the modal, per the dark-card contract. */
function Surface({
  label,
  children,
  glass = false,
}: {
  label?: string;
  children: ReactNode;
  glass?: boolean;
}) {
  return (
    <section
      className={`flex flex-col gap-3 rounded-2xl p-4 ${glass ? "bg-zinc-800/40" : "bg-zinc-800"}`}
    >
      {label && <p className="text-xs text-zinc-500">{label}</p>}
      {children}
    </section>
  );
}

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
            className={selected ? undefined : "bg-zinc-900"}
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

/** Flags stay whole (a hyphen is a soft-wrap point, so `--token` would split
 * as `-` / `-token`); only the opaque code may break mid-word. */
function CommandBlock({ command }: { command: string }) {
  return (
    <div className="flex items-center gap-3 rounded-xl bg-zinc-900 py-2 pr-2 pl-3">
      <code className="min-w-0 flex-1 text-primary text-sm">
        {command.split(" ").map((part, index, parts) => (
          <span
            key={part}
            className={
              parts[index - 1] === "--token"
                ? "wrap-anywhere"
                : "whitespace-nowrap"
            }
          >
            {index > 0 ? " " : ""}
            {part}
          </span>
        ))}
      </code>
      <CopyButton textToCopy={command} />
    </div>
  );
}

function CodeStatus({
  text,
  action,
  onAction,
}: {
  text: string;
  action: string;
  onAction: () => void;
}) {
  return (
    <div className="flex items-center justify-between gap-3 rounded-xl bg-zinc-900 p-3 text-sm text-zinc-400">
      <span>{text}</span>
      <Button size="sm" color="primary" onPress={onAction}>
        {action}
      </Button>
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
      <ModalHeader>Import browser logins</ModalHeader>
      <ModalBody className="gap-3">
        <Surface label="Browser">
          <BrowserPicker value={browser} onChange={setBrowser} />
        </Surface>

        <Surface label="Run in Terminal">
          {isMinting || (!command && !error && !isExpired) ? (
            <Skeleton className="h-10 w-full rounded-xl" />
          ) : error ? (
            <CodeStatus
              text="Couldn't get a code."
              action="Try again"
              onAction={mint}
            />
          ) : isExpired || !command ? (
            <CodeStatus
              text="Code expired."
              action="New code"
              onAction={mint}
            />
          ) : (
            <>
              <CommandBlock command={command} />
              <p
                className={`text-xs ${secondsLeft <= EXPIRY_WARNING_SECONDS ? "text-amber-400/80" : "text-zinc-500"}`}
              >
                Expires in {formatCountdown(secondsLeft)}
              </p>
            </>
          )}
        </Surface>

        <Surface glass>
          <ul className="flex flex-col gap-2">
            {FACTS.map((fact) => (
              <li key={fact} className="flex items-center gap-2.5">
                <span className="size-1.5 shrink-0 rounded-full bg-zinc-600" />
                <span className="text-xs text-zinc-400">{fact}</span>
              </li>
            ))}
          </ul>
        </Surface>
      </ModalBody>
      <ModalFooter className="items-center justify-between">
        <p className="min-w-0 text-xs text-zinc-500">
          macOS, Chromium browsers.{" "}
          <Link
            href={GAIA_CONNECT_README_URL}
            isExternal
            size="sm"
            className="text-xs"
          >
            Get gaia-connect
          </Link>
        </p>
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
