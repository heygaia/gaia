"use client";

import { ReactNode } from "react";

import { useHeader as useHeaderStore } from "@/stores/uiStore";

/**
 * Custom hook for managing the header component
 * @returns An object with the current header and function to set it
 */
export const useHeader = () => {
  const { header, setHeader: setHeaderStore } = useHeaderStore();

  /**
   * Sets the header JSX component
   * @param component - React component or JSX element to render as header
   */
  const setHeader = (component: ReactNode) => {
    setHeaderStore(component);
  };

  return {
    header: header.component,
    setHeader,
  };
};
