import { Button } from "@heroui/button";
import { Chip } from "@heroui/chip";
import { Input } from "@heroui/input";
import { SearchIcon } from "lucide-react";
import Link from "next/link";
import { useState } from "react";

import { ScrollArea } from "@/components/ui/shadcn/scroll-area";
import Spinner from "@/components/ui/shadcn/spinner";
import { parseDate } from "@/utils/date/dateUtils";

import { type MessageSearchResult, searchApi } from "../api/searchApi";

export default function Search() {
  const [fetchedResults, setFetchedResults] = useState<MessageSearchResult[]>(
    [],
  );
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [loading, setLoading] = useState<boolean>(false);

  const handleSearch = async () => {
    setLoading(true);
    try {
      const response = await searchApi.searchMessages(searchQuery);
      setFetchedResults(response.results);
    } catch (error) {
      console.error("Error fetching messages:", error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <div className="flex h-full flex-col justify-between">
        <ScrollArea>
          <div className="flex flex-col items-center gap-2">
            <h1 className="text-center text-5xl font-bold">Search</h1>
            <div className="text-md max-w-(--breakpoint-md) pb-6 text-center">
              Lorem, ipsum dolor sit amet consectetur adipisicing elit. Facilis,
              sed!
            </div>
          </div>

          {loading ? (
            <div className="flex h-[80vh] items-center justify-center">
              <Spinner />
            </div>
          ) : (
            <div className="flex flex-wrap justify-center gap-4 pb-8">
              <div>
                {!!fetchedResults && fetchedResults?.length > 0 ? (
                  <div className="grid grid-cols-[repeat(auto-fill,minmax(15vw,1fr))] gap-3 px-[10%]">
                    {fetchedResults.map((result) => (
                      <Link
                        key={result.message.message_id}
                        className="flex h-full max-h-[190px] min-h-[190px] flex-col gap-2 overflow-hidden rounded-xl bg-black p-3 outline-2 outline-zinc-800 transition-colors hover:bg-zinc-800"
                        href={{
                          pathname: `/c/${result.conversation_id}`,
                          query: { messageId: result.message.message_id },
                        }}
                      >
                        <Chip
                          className="min-h-7"
                          color={
                            result.message.type == "bot" ? "primary" : "default"
                          }
                        >
                          {result.message.type == "bot"
                            ? "From GAIA"
                            : "From You"}
                        </Chip>

                        <div className="max-h-[140px] overflow-hidden text-sm">
                          {result.message?.response?.slice(0, 350)}
                          {result?.message?.response?.length > 350 ? "..." : ""}
                        </div>
                        <div className="mt-auto text-xs text-foreground-400">
                          {parseDate(result?.message?.date)}
                        </div>
                      </Link>
                    ))}
                  </div>
                ) : (
                  <></>
                )}
              </div>
            </div>
          )}
        </ScrollArea>

        <div className="absolute bottom-5 left-0 z-10 flex w-full items-center justify-center">
          <div className="flex w-full max-w-(--breakpoint-sm) items-center gap-3">
            <Input
              autoFocus
              className="w-full"
              classNames={{ inputWrapper: "pr-1" }}
              endContent={
                <Button
                  isIconOnly
                  color="primary"
                  radius="full"
                  onClick={handleSearch}
                >
                  <SearchIcon />
                </Button>
              }
              placeholder="Enter a message to search:   "
              radius="full"
              size="lg"
              value={searchQuery}
              variant="faded"
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") handleSearch();
              }}
            />
          </div>
        </div>
        <div className="bg-custom-gradient2 absolute bottom-0 left-0 z-1 h-[100px] w-full" />
      </div>
    </>
  );
}
