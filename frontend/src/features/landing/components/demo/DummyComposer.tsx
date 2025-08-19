import { Button } from "@heroui/button";
import { Textarea } from "@heroui/input";
import { Kbd } from "@heroui/react";
import { Tooltip } from "@heroui/tooltip";
import { ArrowUp, ChevronRight } from "lucide-react";
import { WrenchIcon } from "lucide-react";
import Image from "next/image";
import React, { useRef, useState } from "react";

import { AttachmentIcon, PlusSignIcon } from "@/components/shared/icons";
import { Button as ShadcnButton } from "@/components/ui/shadcn/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/shadcn/dropdown-menu";

import DummySlashCommandDropdown from "./DummySlashCommandDropdown";

// Dummy integrations data for the top banner
const dummyIntegrations = [
  {
    id: "gmail",
    name: "Gmail",
    icons: ["/icons/gmail.svg"],
  },
  {
    id: "google-calendar",
    name: "Google Calendar",
    icons: ["/icons/googlecalendar.webp"],
  },
  {
    id: "google-docs",
    name: "Google Docs",
    icons: ["/icons/google_docs.webp"],
  },
  {
    id: "notion",
    name: "Notion",
    icons: ["/icons/notion.webp"],
  },
];

const DummyComposer: React.FC = () => {
  const [message, setMessage] = useState("");
  const [isSlashDropdownOpen, setIsSlashDropdownOpen] = useState(true);

  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const composerRef = useRef<HTMLDivElement>(null);

  const handleInputChange = (value: string) => {
    setMessage(value);
  };

  const handleSlashButtonClick = () => {
    setIsSlashDropdownOpen(!isSlashDropdownOpen);
  };

  const handleIntegrationsClick = () => {
    setIsSlashDropdownOpen(!isSlashDropdownOpen);
  };

  const handleSend = () => {
    if (message.trim()) {
      console.log("Sending message:", message);
      setMessage("");
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="mx-auto flex w-full max-w-7xl flex-col items-center">
      {/* Slash Command Dropdown */}
      <div className="searchbar relative top-2 w-full">
        <DummySlashCommandDropdown
          isVisible={isSlashDropdownOpen}
          onClose={() => setIsSlashDropdownOpen(false)}
          position={{ top: 0, left: 0, width: 400 }}
          openedViaButton={true}
        />
      </div>

      {/* Composer */}
      <div className="searchbar_container relative w-full pb-1">
        {/* Integration Banner */}
        <Button
          className="absolute -top-4 z-[0] flex h-fit w-[92%] rounded-full bg-zinc-800/40 px-4 py-2 pb-8 text-xs text-foreground-300 hover:bg-zinc-800/70 hover:text-zinc-400 sm:w-[46%]"
          onPress={handleIntegrationsClick}
        >
          <div className="flex w-full items-center justify-between">
            <span className="text-xs">Connect your tools to GAIA</span>
            <div className="ml-3 flex items-center gap-1">
              {dummyIntegrations.slice(0, 4).map((integration) => (
                <div
                  key={integration.id}
                  className="opacity-60 transition duration-200 hover:scale-150 hover:rotate-6 hover:opacity-120"
                  title={integration.name}
                >
                  <Image
                    width={14}
                    height={14}
                    src={integration.icons[0]}
                    alt={integration.name}
                    className="h-[14px] w-[14px] object-contain"
                  />
                </div>
              ))}
              <ChevronRight width={18} height={18} className="ml-3" />
            </div>
          </div>
        </Button>

        {/* Main Composer */}
        <div
          ref={composerRef}
          className="searchbar relative z-[2] rounded-3xl bg-zinc-800 px-1 pt-1 pb-2"
        >
          {/* Textarea Input */}
          <form
            onSubmit={(e) => {
              e.preventDefault();
              handleSend();
            }}
          >
            <Textarea
              ref={textareaRef}
              autoFocus
              classNames={{
                inputWrapper:
                  "px-3 data-[hover=true]:bg-zinc-800 group-data-[focus-visible=true]:ring-zinc-800 group-data-[focus-visible=true]:ring-offset-0",
                innerWrapper: "items-center",
                input: "font-light",
              }}
              maxRows={13}
              minRows={1}
              placeholder="What can I do for you today?"
              size="lg"
              value={message}
              onValueChange={handleInputChange}
              onKeyDown={handleKeyPress}
              endContent={
                <div className="flex items-center gap-1 text-xs text-nowrap text-foreground-500">
                  <Kbd className="bg-zinc-700">/</Kbd>
                  for tools
                </div>
              }
            />
          </form>

          {/* Toolbar */}
          <div className="flex items-center justify-between px-2 pt-1">
            <div className="flex items-center justify-start gap-2">
              {/* Add Context Dropdown */}
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <ShadcnButton
                    size="icon"
                    className="group relative h-9 w-9 rounded-full border-none bg-zinc-700 p-0 hover:bg-zinc-600/90"
                  >
                    <PlusSignIcon className="min-h-[23px] min-w-[23px] text-zinc-400!" />
                    <span
                      className="absolute -top-0 -right-0 h-2 w-2 rounded-full bg-primary opacity-0 transition"
                      aria-hidden="true"
                    />
                  </ShadcnButton>
                </DropdownMenuTrigger>
                <DropdownMenuContent
                  align="end"
                  side="top"
                  className="w-fit gap-2 rounded-xl border-none bg-zinc-900 p-1 text-white outline-2! outline-zinc-800!"
                >
                  <Tooltip
                    content={
                      <div className="max-w-[270px]">
                        Upload and analyze documents, images or other files
                      </div>
                    }
                    color="foreground"
                    radius="sm"
                  >
                    <DropdownMenuItem className="cursor-pointer rounded-lg px-3 py-2 focus:bg-zinc-800 focus:text-white">
                      <div className="flex w-full items-center justify-between gap-3">
                        <div className="flex flex-col">
                          <div className="flex flex-row items-center gap-2">
                            <AttachmentIcon className="min-h-[20px] min-w-[20px] text-primary" />
                            <span>Attach Files</span>
                          </div>
                        </div>
                      </div>
                    </DropdownMenuItem>
                  </Tooltip>
                </DropdownMenuContent>
              </DropdownMenu>

              {/* Tools Button */}
              <Tooltip
                content="Browse all tools"
                placement="right"
                color="primary"
                showArrow
              >
                <ShadcnButton
                  size="icon"
                  className={`group w- relative h-9 rounded-full border-none bg-zinc-700 p-0 text-zinc-400 hover:bg-zinc-600/90 ${
                    isSlashDropdownOpen &&
                    "border-primary/50 bg-primary/20 text-primary"
                  }`}
                  onClick={handleSlashButtonClick}
                >
                  <WrenchIcon
                    className="min-h-[20px] min-w-[20px]"
                    color={undefined}
                  />
                  {isSlashDropdownOpen && (
                    <span
                      className="absolute top-0 right-0 h-2 w-2 rounded-full bg-primary transition"
                      aria-hidden="true"
                    />
                  )}
                </ShadcnButton>
              </Tooltip>
            </div>

            {/* Send Button */}
            <ShadcnButton
              type="submit"
              onClick={handleSend}
              disabled={!message.trim()}
              className="h-9 w-9 rounded-full bg-primary p-0 text-xl hover:bg-primary/90 disabled:opacity-50"
            >
              <ArrowUp width={40} height={40} className="min-h-5 min-w-5" />
            </ShadcnButton>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DummyComposer;
