import { create } from "zustand";

import { ImageResult } from "@/types/features/convoTypes";

interface ImageDialogState {
  isOpen: boolean;
  selectedImage: ImageResult | null;
  openImageDialog: (image: ImageResult) => void;
  closeImageDialog: () => void;
}

export const useImageDialogStore = create<ImageDialogState>((set) => ({
  isOpen: false,
  selectedImage: null,
  openImageDialog: (image: ImageResult) =>
    set({
      isOpen: true,
      selectedImage: image,
    }),
  closeImageDialog: () =>
    set({
      isOpen: false,
      selectedImage: null,
    }),
}));
