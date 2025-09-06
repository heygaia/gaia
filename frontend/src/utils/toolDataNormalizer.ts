/**
 * Utility functions for handling tool data with multiple instances
 *
 * ARCHITECTURE NOTE:
 * =================
 * Backend accumulates multiple tool calls as arrays:
 * - Single tool call: tool_data = [data]
 * - Multiple tool calls: tool_data = [data1, data2, data3]
 * - Multiple calls with arrays: tool_data = [[arr1], [arr2], [arr3]]
 *
 * Frontend renders all instances to show complete tool output.
 */

import React from "react";

/**
 * Render helper that handles arrays and returns JSX for each item
 * This ensures all tool data instances are rendered
 */
export function renderToolData<T>(
  data: T | T[] | null | undefined,
  renderFn: (item: T, index: number) => React.ReactNode,
): React.ReactNode[] {
  if (!data) return [];

  if (Array.isArray(data)) {
    return data.map((item, index) => renderFn(item, index));
  }

  return [renderFn(data, 0)];
}

/**
 * Helper for array-based tool data (like email_fetch_data)
 * Handles both arrays and arrays-of-arrays consistently
 * 
 * IMPORTANT: This strictly follows the backend format:
 * - Single call: [[array1]]
 * - Multiple calls: [[array1], [array2], [array3]]
 */
export function renderArrayToolData<T>(
  data: T[] | T[][] | null | undefined,
  renderFn: (items: T[], index: number) => React.ReactNode,
): React.ReactNode[] {
  if (!data) return [];

  // Check if it's array of arrays by checking first element
  if (data.length > 0 && Array.isArray(data[0])) {
    // Array of arrays: [[item1, item2], [item3, item4]]
    return (data as T[][]).map((items, index) => renderFn(items, index));
  }

  // Single array: [item1, item2, item3]
  return [renderFn(data as T[], 0)];
}
