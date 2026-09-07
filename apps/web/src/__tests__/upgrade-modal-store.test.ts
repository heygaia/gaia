import { beforeEach, describe, expect, it } from "vitest";

import { useUpgradeModalStore } from "@/stores/upgradeModalStore";

describe("upgradeModalStore", () => {
  beforeEach(() => {
    useUpgradeModalStore.setState({
      open: false,
      offer: null,
      dismissible: false,
    });
  });

  it("starts closed with no offer", () => {
    const state = useUpgradeModalStore.getState();
    expect(state.open).toBe(false);
    expect(state.offer).toBeNull();
    expect(state.dismissible).toBe(false);
  });

  it("opens with no offer when called with none (composer/toggle call sites)", () => {
    useUpgradeModalStore.getState().openModal();

    const state = useUpgradeModalStore.getState();
    expect(state.open).toBe(true);
    expect(state.offer).toBeNull();
  });

  it("defaults to non-dismissible when no options are passed (every enforcement call site)", () => {
    useUpgradeModalStore.getState().openModal();

    expect(useUpgradeModalStore.getState().dismissible).toBe(false);
  });

  it("defaults to non-dismissible even when an offer is passed without options (402 interceptor)", () => {
    useUpgradeModalStore.getState().openModal({
      checkoutUrl: "https://checkout.example/session",
      discountCode: null,
    });

    expect(useUpgradeModalStore.getState().dismissible).toBe(false);
  });

  it("opens dismissible when explicitly requested (voluntary upgrade entry points)", () => {
    useUpgradeModalStore.getState().openModal(undefined, { dismissible: true });

    const state = useUpgradeModalStore.getState();
    expect(state.open).toBe(true);
    expect(state.dismissible).toBe(true);
  });

  it("resets dismissible back to false on close", () => {
    useUpgradeModalStore.getState().openModal(undefined, { dismissible: true });
    useUpgradeModalStore.getState().closeModal();

    expect(useUpgradeModalStore.getState().dismissible).toBe(false);
  });

  it("carries the 402 payload through openModal", () => {
    useUpgradeModalStore.getState().openModal({
      checkoutUrl: "https://checkout.example/session",
      discountCode: "LAUNCH20",
      message: "Subscribe to keep chatting",
    });

    const state = useUpgradeModalStore.getState();
    expect(state.open).toBe(true);
    expect(state.offer).toEqual({
      checkoutUrl: "https://checkout.example/session",
      discountCode: "LAUNCH20",
      message: "Subscribe to keep chatting",
    });
  });

  it("clears open and offer on close", () => {
    useUpgradeModalStore.getState().openModal(
      { checkoutUrl: null, discountCode: "X" },
      {
        dismissible: true,
      },
    );

    useUpgradeModalStore.getState().closeModal();

    const state = useUpgradeModalStore.getState();
    expect(state.open).toBe(false);
    expect(state.offer).toBeNull();
  });

  it("refuses to close an enforcement-mode modal", () => {
    useUpgradeModalStore.getState().openModal({ checkoutUrl: null });

    useUpgradeModalStore.getState().closeModal();

    expect(useUpgradeModalStore.getState().open).toBe(true);
  });

  it("closes an enforcement-mode modal when forced (paid flip, popup mirror)", () => {
    useUpgradeModalStore.getState().openModal({ checkoutUrl: null });

    useUpgradeModalStore.getState().closeModal({ force: true });

    const state = useUpgradeModalStore.getState();
    expect(state.open).toBe(false);
    expect(state.offer).toBeNull();
  });
});
