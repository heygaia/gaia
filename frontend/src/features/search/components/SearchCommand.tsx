"use client";

import { Chip } from "@heroui/chip";
import { ArrowTopRightIcon } from "@radix-ui/react-icons";
import { Lightbulb } from "lucide-react";
import { usePathname, useRouter } from "next/navigation";
import {
  type Dispatch,
  type SetStateAction,
  useCallback,
  useEffect,
  useState,
} from "react";

import {
  BubbleChatIcon,
  BubbleConversationChatIcon,
  Calendar01Icon,
  DiscoverCircleIcon,
  PencilEdit02Icon,
  PinIcon,
  Route02Icon,
  StickyNote01Icon,
  Tick02Icon,
} from "@/components/shared/icons";
import {
  CommandDialog,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
  CommandSeparator,
} from "@/components/ui/shadcn/command";

import { ComprehensiveSearchResponse, searchApi } from "../api/searchApi";
import { SearchCard } from "./SearchCard";

const pages = [
  {
    path: "/explore",
    icon: (
      <DiscoverCircleIcon
        className="min-h-[22px] min-w-[22px]"
        color="#9b9b9b"
      />
    ),
    name: "Go to Explore",
  },
  {
    path: "/pins",
    icon: <PinIcon className="min-h-[22px] min-w-[22px]" color="#9b9b9b" />,
    name: "Go to Pins",
  },
  {
    path: "/calendar",
    icon: (
      <Calendar01Icon className="min-h-[22px] min-w-[22px]" color="#9b9b9b" />
    ),
    name: "Go to Calendar",
  },
  {
    path: "/notes",
    icon: (
      <StickyNote01Icon className="min-h-[22px] min-w-[22px]" color="#9b9b9b" />
    ),
    name: "Go to Notes",
  },
  {
    path: "/goals",
    icon: <Route02Icon className="min-h-[22px] min-w-[22px]" color="#9b9b9b" />,
    name: "Go to Goals",
  },
];

const commands = [
  {
    name: "New Chat",
    action: () => console.log("Create new note"),
    icon: (
      <PencilEdit02Icon className="min-h-[22px] min-w-[22px]" color="#9b9b9b" />
    ),
  },
];

export default function SearchCommand({
  openSearchDialog,
  setOpenSearchDialog,
}: {
  openSearchDialog: boolean;
  setOpenSearchDialog: Dispatch<SetStateAction<boolean>>;
}) {
  const [searchQuery, setSearchQuery] = useState("");

  const [filteredPages, setFilteredPages] = useState(pages);
  const [filteredCommands, setFilteredCommands] = useState(commands);
  const router = useRouter();
  const pathname = usePathname();
  const [results, setResults] = useState<ComprehensiveSearchResponse>({
    conversations: [],
    messages: [],
    notes: [],
  });
  const [chipsVisibility, setChipsVisibility] = useState({
    messages: true,
    conversations: true,
    notes: true,
  });

  useEffect(() => {
    const down = (e: KeyboardEvent) => {
      if (e.key === "k" && (e.metaKey || e.ctrlKey)) {
        e.preventDefault();
        setOpenSearchDialog((open) => !open);
      }
    };

    document.addEventListener("keydown", down);

    return () => document.removeEventListener("keydown", down);
  }, [setOpenSearchDialog]);

  useEffect(() => {
    setOpenSearchDialog(false);
  }, [pathname, setOpenSearchDialog]);

  const handleChipClick = (type: "conversations" | "messages" | "notes") => {
    setChipsVisibility((prevVisibilities) => ({
      ...prevVisibilities,
      [type]: !prevVisibilities[type],
    }));
  };

  const handleSearch = useCallback(async () => {
    if (!searchQuery.trim()) {
      setResults({
        conversations: [],
        messages: [],
        notes: [],
      });

      return;
    }
    try {
      const response = await searchApi.search(searchQuery);

      setResults({
        conversations: response.conversations,
        messages: response.messages,
        notes: response.notes,
      });
    } catch (error) {
      console.error("Error fetching search results:", error);
      setResults({
        conversations: [],
        messages: [],
        notes: [],
      });
    }
  }, [searchQuery]);

  useEffect(() => {
    const delayDebounceFn = setTimeout(() => {
      handleSearch();
      setFilteredPages(
        pages.filter((page) =>
          page.name.toLowerCase().includes(searchQuery.toLowerCase()),
        ),
      );
      setFilteredCommands(
        commands.filter((command) =>
          command.name.toLowerCase().includes(searchQuery.toLowerCase()),
        ),
      );
    }, 200);

    return () => clearTimeout(delayDebounceFn);
  }, [searchQuery, handleSearch]);

  return (
    <CommandDialog open={openSearchDialog} onOpenChange={setOpenSearchDialog}>
      <CommandInput
        placeholder="Search for messages..."
        value={searchQuery}
        onValueChange={setSearchQuery}
      />

      {searchQuery && (
        <div className="flex items-center gap-1 rounded-xl bg-zinc-900 p-2 text-sm font-medium text-foreground-500">
          {(results.messages.length > 0 ||
            results.conversations.length > 0 ||
            results.notes.length > 0) && <span className="mr-2">Filters:</span>}

          {results.messages.length > 0 && (
            <Chip
              // size="sm"
              className="max-h-6 cursor-pointer"
              classNames={{ content: "font-medium" }}
              color={chipsVisibility.messages ? "primary" : "default"}
              endContent={
                chipsVisibility.messages ? (
                  <Tick02Icon color="#000" width={15} height={15} />
                ) : undefined
              }
              startContent={
                <BubbleChatIcon
                  color={chipsVisibility.messages ? "#000000" : "#9b9b9b"}
                  width={15}
                  height={15}
                />
              }
              variant={chipsVisibility.messages ? "solid" : "faded"}
              onClick={() => handleChipClick("messages")}
            >
              Messages
            </Chip>
          )}
          {results.conversations.length > 0 && (
            <Chip
              className="cursor-pointer"
              classNames={{ content: "font-medium min-h-3" }}
              color={chipsVisibility.conversations ? "primary" : "default"}
              endContent={
                chipsVisibility.conversations ? (
                  <Tick02Icon color="#000" width={15} height={15} />
                ) : undefined
              }
              size="sm"
              startContent={
                <BubbleConversationChatIcon
                  color={chipsVisibility.conversations ? "#000000" : "#9b9b9b"}
                  width={15}
                  height={15}
                />
              }
              variant={chipsVisibility.conversations ? "solid" : "faded"}
              onClick={() => handleChipClick("conversations")}
            >
              Conversations
            </Chip>
          )}
          {results.notes.length > 0 && (
            <Chip
              className="cursor-pointer"
              classNames={{ content: "font-medium" }}
              color={chipsVisibility.notes ? "primary" : "default"}
              endContent={
                chipsVisibility.notes ? <Tick02Icon color="#000" /> : undefined
              }
              size="sm"
              startContent={
                <StickyNote01Icon
                  color={chipsVisibility.notes ? "#000000" : "#9b9b9b"}
                  width={15}
                  height={15}
                />
              }
              variant={chipsVisibility.notes ? "solid" : "faded"}
              onClick={() => handleChipClick("notes")}
            >
              Notes
            </Chip>
          )}
        </div>
      )}

      <CommandList className="bg-zinc-900">
        <CommandGroup>
          {filteredCommands.map((command) => (
            <CommandItem
              key={command.name}
              className="group my-3! cursor-pointer rounded-lg hover:bg-zinc-800"
              onSelect={() => {
                setOpenSearchDialog(false);
                command.action();
              }}
            >
              <div className="flex w-full items-center gap-2">
                {command.icon}
                {command.name}
                <ArrowTopRightIcon className="ml-auto text-foreground-500 transition-all group-hover:text-[#00bbff]" />
              </div>
            </CommandItem>
          ))}
        </CommandGroup>
        <CommandSeparator />

        <CommandGroup heading="Pages">
          {filteredPages.map((page) => (
            <CommandItem
              key={page.name}
              className="group cursor-pointer rounded-lg hover:bg-zinc-800"
              onSelect={() => {
                setOpenSearchDialog(false);
                router.push(page.path);
              }}
            >
              <div className="flex w-full items-center gap-2">
                {page.icon}
                {page.name}
                <ArrowTopRightIcon className="ml-auto text-foreground-500 transition-all group-hover:text-[#00bbff]" />
              </div>
            </CommandItem>
          ))}
        </CommandGroup>

        <CommandSeparator />

        {!!searchQuery &&
          chipsVisibility.messages &&
          !!results.messages &&
          results.messages.length > 0 && (
            <CommandGroup heading="Messages">
              {results.messages.map((message, index) => (
                <SearchCard
                  key={index}
                  result={message}
                  type="message"
                  // searchQuery={searchQuery}
                />
              ))}
            </CommandGroup>
          )}

        {!!searchQuery &&
          chipsVisibility.conversations &&
          !!results.conversations &&
          results.conversations.length > 0 && (
            <CommandGroup heading="Conversations">
              {results.conversations.map((conversation, index) => (
                <SearchCard
                  result={conversation}
                  type="conversation"
                  key={index}
                />
              ))}
            </CommandGroup>
          )}

        {!!searchQuery &&
          !!results.notes &&
          chipsVisibility.notes &&
          results.notes.length > 0 && (
            <CommandGroup heading="Notes">
              {results.notes.map((note, index) => (
                <SearchCard key={index} result={note} type="note" />
              ))}
            </CommandGroup>
          )}

        {!!searchQuery &&
          results.conversations.length == 0 &&
          results.messages.length == 0 && (
            <div className="p-3 text-center text-sm">No Results Found</div>
          )}
      </CommandList>

      {/* {!searchQuery && ( */}
      <div className="inline-flex items-center justify-center gap-2 bg-zinc-900 p-2 text-center text-sm text-foreground-500">
        <Lightbulb className="relative left-1 size-[20px] text-white" />
        Tip: Hit
        <kbd className="bg-muted text-muted-foreground pointer-events-none inline-flex h-5 items-center gap-1 rounded bg-zinc-600 px-1.5 font-mono text-[10px] font-medium text-white opacity-100 select-none">
          <span className="text-xs">⌘</span>K
        </kbd>
        to open this Command Menu
      </div>
      {/* // )} */}
    </CommandDialog>
  );
}
