import { Textarea } from "@heroui/input";
import { Kbd } from "@heroui/react";
import React, {
  useCallback,
  useEffect,
  useImperativeHandle,
  useState,
} from "react";

import {
  SlashCommandMatch,
  useSlashCommands,
} from "@/features/chat/hooks/useSlashCommands";

import SlashCommandDropdown from "./SlashCommandDropdown";

interface SearchbarInputProps {
  searchbarText: string;
  onSearchbarTextChange: (text: string) => void;
  handleFormSubmit: (e?: React.FormEvent<HTMLFormElement>) => void;
  handleKeyDown: React.KeyboardEventHandler<HTMLInputElement>;
  currentHeight: number;
  hasMessages: boolean;
  onHeightChange: (height: number) => void;
  inputRef: React.RefObject<HTMLTextAreaElement | null>;
  onSlashCommandSelect?: (toolName: string, toolCategory: string) => void;
}

export interface ComposerInputRef {
  toggleSlashCommandDropdown: () => void;
  isSlashCommandDropdownOpen: () => boolean;
}

const ComposerInput = React.forwardRef<ComposerInputRef, SearchbarInputProps>(
  (
    {
      searchbarText,
      onSearchbarTextChange,
      handleFormSubmit,
      handleKeyDown,
      currentHeight,
      onHeightChange,
      inputRef,
      hasMessages,
      onSlashCommandSelect,
    },
    ref,
  ) => {
    const { detectSlashCommand, getAllTools } = useSlashCommands();
    const [slashCommandState, setSlashCommandState] = useState({
      isActive: false,
      matches: [] as SlashCommandMatch[],
      selectedIndex: 0,
      commandStart: -1,
      commandEnd: -1,
      dropdownPosition: { top: 0, left: 0, width: 0 } as {
        top?: number;
        bottom?: number;
        left: number;
        width: number;
      },
      openedViaButton: false, // Track if dropdown was opened via button
    });

    // Expose methods to parent component
    useImperativeHandle(
      ref,
      () => ({
        toggleSlashCommandDropdown: () => {
          if (slashCommandState.isActive) {
            // Close the dropdown
            setSlashCommandState((prev) => ({
              ...prev,
              isActive: false,
              openedViaButton: false,
            }));
          } else {
            // Open the dropdown
            const allTools = getAllTools();
            const allMatches = allTools.map((tool) => ({
              tool,
              matchedText: "",
            }));

            // Calculate dropdown position - use same logic as normal slash command detection
            const textarea = inputRef.current;
            if (textarea) {
              // Get composer container for proper width
              const composerContainer = textarea.closest(".searchbar");
              const rect =
                composerContainer?.getBoundingClientRect() ||
                textarea.getBoundingClientRect();

              const position = {
                bottom: rect.top, // Position dropdown bottom at composer top
                left: rect.left,
                width: rect.width, // Match the composer width
              };

              setSlashCommandState({
                isActive: true,
                matches: allMatches,
                selectedIndex: 0,
                commandStart: 0,
                commandEnd: 0,
                dropdownPosition: position,
                openedViaButton: true, // Mark as opened via button
              });
            }
          }
        },
        isSlashCommandDropdownOpen: () => slashCommandState.isActive,
      }),
      [getAllTools, inputRef, slashCommandState.isActive],
    );

    const updateSlashCommandDetection = useCallback(
      (text: string, cursorPosition: number) => {
        const detection = detectSlashCommand(text, cursorPosition);

        if (detection.isSlashCommand && detection.matches.length > 0) {
          // Calculate dropdown position - position above the composer and match its width
          const textarea = inputRef.current;
          if (textarea) {
            // Get composer container for proper width
            const composerContainer = textarea.closest(".searchbar");
            const rect =
              composerContainer?.getBoundingClientRect() ||
              textarea.getBoundingClientRect();

            setSlashCommandState({
              isActive: true,
              matches: detection.matches,
              selectedIndex: 0,
              commandStart: detection.commandStart,
              commandEnd: detection.commandEnd,
              dropdownPosition: {
                bottom: rect.top, // Position dropdown bottom at composer top
                left: rect.left,
                width: rect.width, // Match the composer width
              },
              openedViaButton: false, // This is a normal slash command detection
            });
          }
        } else {
          // Only close if it wasn't opened via button, or if no matches when opened via button
          setSlashCommandState((prev) => ({
            ...prev,
            isActive: prev.openedViaButton ? prev.isActive : false,
            matches: prev.openedViaButton ? prev.matches : [],
          }));
        }
      },
      [detectSlashCommand, inputRef],
    );

    const handleSlashCommandSelect = useCallback(
      (match: SlashCommandMatch) => {
        // Remove the slash command portion while keeping other text
        const textBeforeCommand = searchbarText.substring(
          0,
          slashCommandState.commandStart,
        );
        const textAfterCommand = searchbarText.substring(
          slashCommandState.commandEnd,
        );
        const newText = textBeforeCommand + textAfterCommand;

        onSearchbarTextChange(newText);
        setSlashCommandState((prev) => ({
          ...prev,
          isActive: false,
          openedViaButton: false,
        }));

        // Notify parent component about tool selection
        if (onSlashCommandSelect) {
          onSlashCommandSelect(match.tool.name, match.tool.category);
        }

        // Focus back to input and position cursor where the slash command was
        setTimeout(() => {
          if (inputRef.current) {
            const newCursorPos = slashCommandState.commandStart;
            inputRef.current.setSelectionRange(newCursorPos, newCursorPos);
            inputRef.current.focus();
          }
        }, 0);
      },
      [
        searchbarText,
        slashCommandState,
        onSearchbarTextChange,
        onSlashCommandSelect,
        inputRef,
      ],
    );

    const handleSlashCommandKeyDown = useCallback(
      (e: React.KeyboardEvent) => {
        if (!slashCommandState.isActive) return false;

        switch (e.key) {
          case "ArrowUp":
            e.preventDefault();
            setSlashCommandState((prev) => ({
              ...prev,
              selectedIndex: Math.max(0, prev.selectedIndex - 1),
            }));
            return true;

          case "ArrowDown":
            e.preventDefault();
            setSlashCommandState((prev) => ({
              ...prev,
              selectedIndex: Math.min(
                prev.matches.length - 1,
                prev.selectedIndex + 1,
              ),
            }));
            return true;

          case "Enter":
          case "Tab":
            e.preventDefault();
            // If there's only one match, automatically select it regardless of selectedIndex
            if (slashCommandState.matches.length === 1) {
              handleSlashCommandSelect(slashCommandState.matches[0]);
            } else {
              const selectedMatch =
                slashCommandState.matches[slashCommandState.selectedIndex];
              if (selectedMatch) {
                handleSlashCommandSelect(selectedMatch);
              }
            }
            return true;

          case "Escape":
            e.preventDefault();
            setSlashCommandState((prev) => ({
              ...prev,
              isActive: false,
              openedViaButton: false,
            }));
            return true;

          default:
            return false;
        }
      },
      [slashCommandState, handleSlashCommandSelect],
    );

    const handleTextChange = useCallback(
      (text: string) => {
        onSearchbarTextChange(text);

        // Update slash command detection
        setTimeout(() => {
          if (inputRef.current) {
            const cursorPosition = inputRef.current.selectionStart || 0;
            updateSlashCommandDetection(text, cursorPosition);
          }
        }, 0);
      },
      [onSearchbarTextChange, updateSlashCommandDetection, inputRef],
    );

    const handleKeyDownWithSlashCommands: React.KeyboardEventHandler<HTMLInputElement> =
      useCallback(
        (e) => {
          // First, handle slash command navigation
          const wasHandledBySlashCommand = handleSlashCommandKeyDown(e);

          // If not handled by slash command, pass to original handler
          if (!wasHandledBySlashCommand) {
            handleKeyDown(e);
          }
        },
        [handleSlashCommandKeyDown, handleKeyDown],
      );

    // Update cursor position tracking
    const handleCursorPositionChange = useCallback(() => {
      if (inputRef.current) {
        const cursorPosition = inputRef.current.selectionStart || 0;
        updateSlashCommandDetection(searchbarText, cursorPosition);
      }
    }, [searchbarText, updateSlashCommandDetection, inputRef]);

    // Close dropdown when clicking outside
    useEffect(() => {
      const handleClickOutside = (event: MouseEvent) => {
        const target = event.target as Element;

        // Don't close if clicking inside the dropdown or the input
        if (
          target.closest(".slash-command-dropdown") ||
          target.closest(".searchbar") ||
          inputRef.current?.contains(target)
        ) {
          return;
        }

        setSlashCommandState((prev) => ({
          ...prev,
          isActive: false,
          openedViaButton: false,
        }));
      };

      if (slashCommandState.isActive) {
        document.addEventListener("click", handleClickOutside);
        return () => document.removeEventListener("click", handleClickOutside);
      }
    }, [slashCommandState.isActive, inputRef]);

    return (
      <>
        {slashCommandState.isActive && (
          <div className="bg-black/05 pointer-events-none fixed top-0 left-0 z-[-1] h-screen w-screen backdrop-blur-xs" />
        )}

        <form onSubmit={handleFormSubmit}>
          <Textarea
            ref={inputRef}
            autoFocus
            classNames={{
              inputWrapper:
                " px-3 data-[hover=true]:bg-zinc-800 group-data-[focus-visible=true]:ring-zinc-800 group-data-[focus-visible=true]:ring-offset-0",
              innerWrapper: `${currentHeight > 24 ? "items-end" : "items-center"}`,
              input: "font-light",
            }}
            isInvalid={searchbarText.length > 10_000}
            maxRows={13}
            minRows={1}
            placeholder="What can I do for you today?"
            size="lg"
            value={searchbarText}
            onHeightChange={onHeightChange}
            onKeyDown={handleKeyDownWithSlashCommands}
            onValueChange={handleTextChange}
            onSelect={handleCursorPositionChange}
            onClick={handleCursorPositionChange}
            endContent={
              <div className="flex items-center gap-1 text-xs text-nowrap text-foreground-500">
                <Kbd className="bg-zinc-700">/</Kbd>
                for tools
              </div>
            }
          />
        </form>

        <SlashCommandDropdown
          matches={slashCommandState.matches}
          selectedIndex={slashCommandState.selectedIndex}
          onSelect={handleSlashCommandSelect}
          onClose={() =>
            setSlashCommandState((prev) => ({
              ...prev,
              isActive: false,
              openedViaButton: false,
            }))
          }
          position={slashCommandState.dropdownPosition}
          isVisible={slashCommandState.isActive}
          openedViaButton={slashCommandState.openedViaButton}
        />
      </>
    );
  },
);

ComposerInput.displayName = "ComposerInput";

export default ComposerInput;
