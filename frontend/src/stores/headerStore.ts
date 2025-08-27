import { create } from "zustand";

export type HeaderComponentType =
  | "chat"
  | "mail"
  | "goals"
  | "calendar"
  | "browser"
  | "notes"
  | "settings"
  | "custom"
  | "default"
  | "todos";

export interface HeaderProps {
  customContent?: boolean;
  jsxContent?: boolean;
  componentProps?: Record<string, unknown>;
  [key: string]: unknown;
}

interface HeaderState {
  currentHeaderType: HeaderComponentType;
  headerProps: HeaderProps | null;
  setHeaderComponent: (params: {
    headerType: HeaderComponentType;
    props?: HeaderProps;
  }) => void;
}

export const useHeaderStore = create<HeaderState>((set) => ({
  currentHeaderType: "default",
  headerProps: null,

  setHeaderComponent: ({ headerType, props }) =>
    set({
      currentHeaderType: headerType,
      headerProps: props || null,
    }),
}));
