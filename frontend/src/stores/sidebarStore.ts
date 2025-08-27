import { create } from "zustand";

export interface SidebarState {
  isOpen: boolean;
  isMobileOpen: boolean;
  variant:
    | "default"
    | "chat"
    | "mail"
    | "todos"
    | "calendar"
    | "notes"
    | "goals";
}

interface SidebarStore extends SidebarState {
  toggleSidebar: () => void;
  setSidebarOpen: (isOpen: boolean) => void;
  toggleMobileSidebar: () => void;
  setMobileSidebarOpen: (isMobileOpen: boolean) => void;
  setSidebarVariant: (variant: SidebarState["variant"]) => void;
}

export const useSidebarStore = create<SidebarStore>((set) => ({
  isOpen: true,
  isMobileOpen: false,
  variant: "default",

  toggleSidebar: () => set((state) => ({ isOpen: !state.isOpen })),
  setSidebarOpen: (isOpen: boolean) => set({ isOpen }),
  toggleMobileSidebar: () =>
    set((state) => ({ isMobileOpen: !state.isMobileOpen })),
  setMobileSidebarOpen: (isMobileOpen: boolean) => set({ isMobileOpen }),
  setSidebarVariant: (variant: SidebarState["variant"]) => set({ variant }),
}));
