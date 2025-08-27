import { create } from "zustand";

interface LoginModalState {
  open: boolean;
  setLoginModalOpen: (open: boolean) => void;
}

export const useLoginModalStore = create<LoginModalState>((set) => ({
  open: false,
  setLoginModalOpen: (open: boolean) => set({ open }),
}));
