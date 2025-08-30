"use client";

import { ReactNode, useCallback } from "react";

import {
  HeaderComponentType,
  HeaderProps,
  useHeader as useHeaderStore,
} from "@/stores/uiStore";

/**
 * Custom hook for managing the header component
 * @returns An object with the current header component type and function to set it
 */
export const useHeader = () => {
  const { currentHeaderType, headerProps, setHeaderComponent } =
    useHeaderStore();

  /**
   * Sets the header component type and props
   * This function can be used in two ways:
   * 1. With a header type: setHeader("notes", { props })
   * 2. With JSX content: setHeader(<CustomHeader prop1="value" />)
   */
  const setHeader = useCallback(
    (
      headerTypeOrJSX: HeaderComponentType | ReactNode,
      props?: Omit<HeaderProps, "componentProps"> & {
        componentProps?: Record<string, unknown>;
      },
    ) => {
      // If the first argument is a string (header type)
      if (typeof headerTypeOrJSX === "string") {
        setHeaderComponent(headerTypeOrJSX as HeaderComponentType, {
          ...props,
          componentProps: props?.componentProps || {},
        });
      }
      // If the first argument is JSX, store it as custom content in the props
      else {
        setHeaderComponent("custom", {
          customContent: true,
          jsxContent: true,
          componentProps: props?.componentProps || {},
          ...props,
        });

        // Store the JSX reference in a module-level variable that HeaderManager can access
        window.__customHeaderJSX = headerTypeOrJSX;
      }
    },
    [setHeaderComponent],
  );

  return {
    currentHeaderType,
    headerProps,
    setHeader,
  };
};
