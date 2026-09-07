"use client";

import { useEffect } from "react";
import { useLogout } from "@/features/auth/hooks/useLogout";
import { usePathname } from "@/i18n/navigation";
import { ANALYTICS_EVENTS, trackEvent } from "@/lib/analytics";
import { useUpgradeModalStore } from "@/stores/upgradeModalStore";

import { paywallCopyFor } from "../constants";
import { isProPlan } from "../utils/planPredicates";
import { useDodoPayments } from "./useDodoPayments";
import { useIsPaid } from "./useIsPaid";
import { usePricing } from "./usePricing";

export function useUpgradeModal() {
  const { open, offer, dismissible, closeModal } = useUpgradeModalStore();
  const pathname = usePathname();
  const { plans } = usePricing();
  const { logout } = useLogout();
  const { openCheckoutOverlay, checkoutPhase } = useDodoPayments();
  const {
    isPaid,
    isUnknown: isSubscriptionStatusUnknown,
    hasEverSubscribed,
  } = useIsPaid();
  const copy = paywallCopyFor(hasEverSubscribed);
  const isConfirming =
    checkoutPhase === "confirming" || checkoutPhase === "timeout";

  // A cold-cache render can open this modal while the subscription-status is
  // still unknown (see useComposerSubmit / useWorkflowModalActions — they let
  // the action proceed while unknown rather than trap the user). Once it
  // resolves paid, close the modal immediately: the enforcement mode refuses
  // ordinary closes, so a Pro user who hit this race would otherwise be stuck
  // behind a non-dismissible modal forever.
  useEffect(() => {
    if (open && !isSubscriptionStatusUnknown && isPaid) {
      closeModal({ force: true });
    }
  }, [open, isSubscriptionStatusUnknown, isPaid, closeModal]);

  // The impression, fired once per open rather than on every render. The
  // server already captures the 402 that opened it; what it cannot see is
  // whether the wall reached the screen, so this is the one client-only half.
  useEffect(() => {
    if (!open) return;
    trackEvent(ANALYTICS_EVENTS.PAYWALL_MODAL_VIEWED, {
      dismissible,
      has_checkout_url: Boolean(offer?.checkoutUrl),
      has_discount_code: Boolean(offer?.discountCode),
    });
  }, [open, dismissible, offer?.checkoutUrl, offer?.discountCode]);

  // Monthly Pro is the default enforcement offer — same tier PricingCards
  // leads with, just without the billing-period tabs (that mode has one job).
  const proPlan = plans.find(
    (plan) => isProPlan(plan) && plan.duration === "monthly",
  );

  const handleSubscribe = () => {
    void openCheckoutOverlay("monthly", { source: "paywall_modal" });
  };

  return {
    open,
    offerMessage: offer?.message,
    discountCode: offer?.discountCode,
    discountPercent: offer?.discountPercent,
    dismissible,
    closeModal,
    plans,
    proPlan,
    copy,
    isConfirming,
    checkoutPhase,
    handleSubscribe,
    logout,
    // The wizard owns payment on its own stage; a 402 from a background request
    // there must not stack this modal on top of it.
    isOnboardingRoute: pathname === "/onboarding",
  };
}
