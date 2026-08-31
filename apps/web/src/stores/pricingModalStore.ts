import { create } from "zustand";
import { devtools } from "zustand/middleware";

/**
 * An offer the modal was opened with — the founder's letter, for one. The code
 * rides along to the Dodo checkout session so it is already applied when the
 * page loads, and the percentage lets the cards show what the reader will
 * actually pay.
 */
export interface PricingOffer {
  discountCode: string;
  discountPercent: number;
}

interface PricingModalStore {
  open: boolean;
  /**
   * Optional context-specific pitch shown above the plan cards (e.g. a
   * staged-work quota pitch from a 402 response). `null` renders the
   * modal's default copy.
   */
  pitch: string | null;
  offer: PricingOffer | null;
  openModal: (arg?: string | PricingOffer) => void;
  closeModal: () => void;
}

export const usePricingModalStore = create<PricingModalStore>()(
  devtools(
    (set) => ({
      open: false,
      pitch: null,
      offer: null,
      openModal: (arg) =>
        set(
          {
            open: true,
            pitch: typeof arg === "string" ? arg : null,
            offer: typeof arg === "object" ? (arg ?? null) : null,
          },
          false,
          "openModal",
        ),
      closeModal: () =>
        set({ open: false, pitch: null, offer: null }, false, "closeModal"),
    }),
    { name: "pricingModal-store" },
  ),
);
