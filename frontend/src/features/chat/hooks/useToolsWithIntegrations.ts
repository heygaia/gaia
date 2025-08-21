import { useQuery } from "@tanstack/react-query";
import { useMemo } from "react";

import { useIntegrations } from "@/features/integrations/hooks/useIntegrations";

import { fetchAvailableTools, ToolInfo } from "../api/toolsApi";
import { EnhancedToolInfo } from "../types/enhancedTools";

export interface UseToolsWithIntegrationsReturn {
  tools: EnhancedToolInfo[];
  toolsByCategory: Record<string, EnhancedToolInfo[]>;
  isLoading: boolean;
  error: Error | null;
  categories: string[];
  getToolsForCategory: (category: string) => EnhancedToolInfo[];
  isToolLocked: (toolName: string) => boolean;
  getLockedToolsCount: () => number;
  getUnlockedToolsCount: () => number;
}

/**
 * Hook that combines tool information with integration status
 * to determine which tools are locked/available
 */
export const useToolsWithIntegrations = (): UseToolsWithIntegrationsReturn => {
  const { getIntegrationsWithStatus } = useIntegrations();

  // Fetch tools data
  const {
    data: toolsData,
    isLoading: toolsLoading,
    error: toolsError,
  } = useQuery({
    queryKey: ["tools"],
    queryFn: fetchAvailableTools,
    staleTime: 60 * 60 * 1000, // Cache for 1 hour
  });

  // Combine tools with integration status
  const enhancedTools = useMemo((): EnhancedToolInfo[] => {
    if (!toolsData?.tools) return [];

    const integrationsWithStatus = getIntegrationsWithStatus();

    return toolsData.tools.map((tool: ToolInfo): EnhancedToolInfo => {
      let isLocked = false;

      if (tool.required_integration) {
        // Check if required integration is connected
        const requiredIntegration = integrationsWithStatus.find(
          (integration) => integration.id === tool.required_integration,
        );

        isLocked =
          !requiredIntegration || requiredIntegration.status !== "connected";
      }

      // Find integration details
      const integrationDetails = integrationsWithStatus.find(
        (integration) => integration.id === tool.required_integration,
      );

      return {
        name: tool.name,
        category: tool.category,
        integration: tool.required_integration
          ? {
              toolName: tool.name,
              category: tool.category,
              requiredIntegration: tool.required_integration,
              integrationName:
                integrationDetails?.name || tool.required_integration,
              isRequired: true,
            }
          : undefined,
        isLocked,
      };
    });
  }, [toolsData?.tools, getIntegrationsWithStatus]);

  // Group tools by category
  const toolsByCategory = useMemo((): Record<string, EnhancedToolInfo[]> => {
    const categorized: Record<string, EnhancedToolInfo[]> = {};

    enhancedTools.forEach((tool) => {
      if (!categorized[tool.category]) {
        categorized[tool.category] = [];
      }
      categorized[tool.category].push(tool);
    });

    // Sort tools within each category (unlocked first, then by name)
    Object.keys(categorized).forEach((category) => {
      categorized[category].sort((a, b) => {
        // Unlocked tools first
        if (a.isLocked !== b.isLocked) {
          return a.isLocked ? 1 : -1;
        }
        // Then alphabetically
        return a.name.localeCompare(b.name);
      });
    });

    return categorized;
  }, [enhancedTools]);

  // Extract categories
  const categories = useMemo((): string[] => {
    return toolsData?.categories || [];
  }, [toolsData?.categories]);

  // Helper functions
  const getToolsForCategory = (category: string): EnhancedToolInfo[] => {
    return toolsByCategory[category] || [];
  };

  const isToolLocked = (toolName: string): boolean => {
    const tool = enhancedTools.find((t) => t.name === toolName);
    return tool?.isLocked || false;
  };

  const getLockedToolsCount = (): number => {
    return enhancedTools.filter((tool) => tool.isLocked).length;
  };

  const getUnlockedToolsCount = (): number => {
    return enhancedTools.filter((tool) => !tool.isLocked).length;
  };

  return {
    tools: enhancedTools,
    toolsByCategory,
    isLoading: toolsLoading,
    error: toolsError,
    categories,
    getToolsForCategory,
    isToolLocked,
    getLockedToolsCount,
    getUnlockedToolsCount,
  };
};
