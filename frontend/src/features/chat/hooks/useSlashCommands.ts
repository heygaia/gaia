import { useCallback } from "react";

import { ToolInfo } from "@/features/chat/api/toolsApi";

import { EnhancedToolInfo } from "../types/enhancedTools";
import { useToolsQuery } from "./useToolsQuery";
import { useToolsWithIntegrations } from "./useToolsWithIntegrations";

export interface SlashCommandMatch {
  tool: ToolInfo;
  enhancedTool?: EnhancedToolInfo;
  matchedText: string;
}

export interface UseSlashCommandsReturn {
  tools: ToolInfo[];
  isLoadingTools: boolean;
  error: string | null;
  detectSlashCommand: (
    text: string,
    cursorPosition: number,
  ) => {
    isSlashCommand: boolean;
    query: string;
    matches: SlashCommandMatch[];
    commandStart: number;
    commandEnd: number;
  };
  getSlashCommandSuggestions: (query: string) => SlashCommandMatch[];
  getAllTools: () => ToolInfo[];
}

export const useSlashCommands = (): UseSlashCommandsReturn => {
  // Use React Query hook for fetching tools with caching
  const { tools, isLoading: isLoadingTools, error } = useToolsQuery();

  // Get enhanced tools with integration status
  const { tools: enhancedTools } = useToolsWithIntegrations();

  const getSlashCommandSuggestions = useCallback(
    (query: string): SlashCommandMatch[] => {
      // If no query, show all tools sorted by unlock status, category and name
      if (!query.trim()) {
        return tools
          .map((tool) => {
            const enhancedTool = enhancedTools.find(
              (et) => et.name === tool.name,
            );
            return {
              tool,
              enhancedTool,
              matchedText: tool.name,
            };
          })
          .sort((a, b) => {
            // Unlocked tools first
            const aLocked = a.enhancedTool?.isLocked || false;
            const bLocked = b.enhancedTool?.isLocked || false;
            if (aLocked !== bLocked) {
              return aLocked ? 1 : -1;
            }

            // Then sort by category, then by name
            if (a.tool.category !== b.tool.category) {
              return a.tool.category.localeCompare(b.tool.category);
            }
            return a.tool.name.localeCompare(b.tool.name);
          });
      }

      const queryLower = query.toLowerCase().trim();
      const matches: SlashCommandMatch[] = [];

      // Find name matches - now supports partial matches with spaces
      tools.forEach((tool) => {
        const enhancedTool = enhancedTools.find((et) => et.name === tool.name);
        const toolNameLower = tool.name.toLowerCase();
        const toolNameSpaced = tool.name.replace(/_/g, " ").toLowerCase();

        if (
          toolNameLower.includes(queryLower) ||
          toolNameSpaced.includes(queryLower)
        ) {
          matches.push({
            tool,
            enhancedTool,
            matchedText: tool.name,
          });
        }
      });

      // Find category matches
      tools.forEach((tool) => {
        const enhancedTool = enhancedTools.find((et) => et.name === tool.name);
        if (
          !matches.find((m) => m.tool.name === tool.name) &&
          tool.category.toLowerCase().includes(queryLower)
        ) {
          matches.push({
            tool,
            enhancedTool,
            matchedText: `${tool.category} tool`,
          });
        }
      });

      // Sort by relevance: exact name matches first, then partial name, then category
      return matches.sort((a, b) => {
        const aNameExact = a.tool.name.toLowerCase() === queryLower;
        const bNameExact = b.tool.name.toLowerCase() === queryLower;
        if (aNameExact && !bNameExact) return -1;
        if (!aNameExact && bNameExact) return 1;

        const aNameStart = a.tool.name.toLowerCase().startsWith(queryLower);
        const bNameStart = b.tool.name.toLowerCase().startsWith(queryLower);
        if (aNameStart && !bNameStart) return -1;
        if (!aNameStart && bNameStart) return 1;

        return a.tool.name.localeCompare(b.tool.name);
      });
    },
    [tools, enhancedTools],
  );

  const detectSlashCommand = useCallback(
    (text: string, cursorPosition: number) => {
      // Find the last slash before the cursor position
      const textBeforeCursor = text.substring(0, cursorPosition);
      const lastSlashIndex = textBeforeCursor.lastIndexOf("/");

      // Check if this is a potential slash command
      if (lastSlashIndex === -1) {
        return {
          isSlashCommand: false,
          query: "",
          matches: [],
          commandStart: -1,
          commandEnd: -1,
        };
      }

      // Check if the slash is at the beginning of the text or preceded by whitespace
      const charBeforeSlash =
        lastSlashIndex > 0 ? text[lastSlashIndex - 1] : " ";
      const isValidSlashPosition =
        lastSlashIndex === 0 || /\s/.test(charBeforeSlash);

      if (!isValidSlashPosition) {
        return {
          isSlashCommand: false,
          query: "",
          matches: [],
          commandStart: -1,
          commandEnd: -1,
        };
      }

      // Check if there's a space immediately after the slash
      const textAfterSlash = text.substring(lastSlashIndex + 1);
      if (textAfterSlash.startsWith(" ")) {
        return {
          isSlashCommand: false,
          query: "",
          matches: [],
          commandStart: -1,
          commandEnd: -1,
        };
      }

      // Find the end of the potential command - extend to next slash or end of text to allow spaces after words
      const nextSlashIndex = textAfterSlash.indexOf("/");
      const commandEnd =
        nextSlashIndex === -1
          ? text.length
          : lastSlashIndex + 1 + nextSlashIndex;

      // Only consider it a slash command if cursor is within the command
      if (cursorPosition > commandEnd) {
        return {
          isSlashCommand: false,
          query: "",
          matches: [],
          commandStart: -1,
          commandEnd: -1,
        };
      }

      const query = text.substring(lastSlashIndex + 1, cursorPosition);
      const matches = getSlashCommandSuggestions(query);

      return {
        isSlashCommand: true,
        query,
        matches,
        commandStart: lastSlashIndex,
        commandEnd,
      };
    },
    [getSlashCommandSuggestions],
  );

  const getAllTools = useCallback(() => {
    return tools;
  }, [tools]);

  return {
    tools,
    isLoadingTools,
    error: error || null,
    detectSlashCommand,
    getSlashCommandSuggestions,
    getAllTools,
  };
};
