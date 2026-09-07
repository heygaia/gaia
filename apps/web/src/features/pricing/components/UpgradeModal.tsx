"use client";

import { Button } from "@heroui/button";
import { Chip } from "@heroui/chip";
import { Modal, ModalBody, ModalContent } from "@heroui/modal";
import { Tab, Tabs } from "@heroui/tabs";
import { Tag01Icon } from "@icons";
import { useEffect } from "react";
import { RaisedButton } from "@/components/ui/raised-button";
import { useLogout } from "@/features/auth/hooks/useLogout";
import { usePathname } from "@/i18n/navigation";
import { ANALYTICS_EVENTS, trackEvent } from "@/lib/analytics";
import { useUpgradeModalStore } from "@/stores/upgradeModalStore";

import { paywallCopyFor } from "../constants";
import { useDodoPayments } from "../hooks/useDodoPayments";
import { useIsPaid } from "../hooks/useIsPaid";
import { usePricing } from "../hooks/usePricing";
import { isCheckoutSettled } from "../stores/checkoutOverlayStore";
import { isProPlan } from "../utils/planPredicates";
import { CheckoutConfirming } from "./CheckoutConfirming";
import { PlanFeature } from "./PlanFeature";
import { PricingCards } from "./PricingCards";

/**
 * The one Pro upsell surface, in both of its modes (see `upgradeModalStore`).
 *
 * Enforcement mode is a compact, undismissable wall around a single monthly
 * Pro CTA — the user cannot proceed, so a plan picker would only be noise.
 * Voluntary mode is the full plan picker (monthly/yearly tabs + cards), since
 * a user who opened this themselves is here to choose.
 */
export function UpgradeModal() {
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

  // The wizard owns payment on its own stage; a 402 from a background request
  // there must not stack this modal on top of it.
  if (pathname === "/onboarding") return null;

  const discountBanner = offer?.discountCode ? (
    <div className="flex items-center gap-2.5 rounded-2xl bg-success/10 px-4 py-2.5 text-success">
      <Tag01Icon width={18} height={18} aria-hidden />
      <p className="text-sm font-normal">
        {offer.discountPercent ? (
          <>
            <span className="font-semibold">{offer.discountPercent}% off</span>{" "}
            is applied with{" "}
            <span className="font-semibold">{offer.discountCode}</span>. The
            prices below are yours.
          </>
        ) : (
          <>
            Use code <span className="font-semibold">{offer.discountCode}</span>{" "}
            at checkout.
          </>
        )}
      </p>
    </div>
  ) : null;

  return (
    <Modal
      size={dismissible ? "full" : "xl"}
      radius="lg"
      isOpen={open}
      onOpenChange={(isOpen) => {
        if (!isOpen) closeModal();
      }}
      isDismissable={dismissible}
      isKeyboardDismissDisabled={!dismissible}
      hideCloseButton={!dismissible}
      backdrop="blur"
      scrollBehavior="inside"
      className="outline-none"
      classNames={{
        wrapper: dismissible ? "overflow-hidden" : undefined,
        closeButton:
          "text-zinc-400 hover:text-white hover:bg-zinc-800 top-3 right-3",
      }}
    >
      <ModalContent className={dismissible ? undefined : "p-4"}>
        {dismissible ? (
          <div className="flex flex-col items-center gap-5 py-8 overflow-y-auto">
            <div className="flex flex-col items-center gap-1.5 text-center">
              <h2 className="font-serif text-5xl font-normal tracking-tight">
                Level Up
              </h2>
              <p className="text-sm font-light text-zinc-400">
                {offer?.message ??
                  "You've been doing this manually. Let GAIA handle it."}
              </p>
            </div>

            {discountBanner}

            <div className="w-full flex flex-col items-center px-5">
              <Tabs aria-label="Billing period" radius="lg">
                <Tab key="monthly" title="Monthly">
                  <p className="mt-3 mb-4 text-center text-xs text-zinc-600">
                    Secure payment · Cancel anytime
                  </p>
                  <PricingCards
                    durationIsMonth
                    initialPlans={plans}
                    hideEnterprise
                  />
                </Tab>
                <Tab
                  key="yearly"
                  title={
                    <div className="flex items-center gap-2">
                      Yearly
                      <Chip color="primary" size="sm" variant="shadow">
                        <span className="text-xs font-medium">
                          2 months free
                        </span>
                      </Chip>
                    </div>
                  }
                >
                  <p className="mt-3 mb-4 text-center text-xs text-zinc-600">
                    Secure payment · Cancel anytime
                  </p>
                  <PricingCards initialPlans={plans} hideEnterprise />
                </Tab>
              </Tabs>
            </div>
          </div>
        ) : (
          <ModalBody>
            <div className="mb-2 flex flex-col items-center gap-1.5 text-center">
              <h2 className="font-serif text-4xl font-normal tracking-tight">
                {copy.heading}
              </h2>
              <p className="text-sm font-light text-zinc-400">
                {offer?.message ?? copy.body}
              </p>
            </div>

            {discountBanner}

            {proPlan && (
              <div className="rounded-2xl bg-zinc-800/50 p-5">
                <div className="flex flex-col gap-2">
                  {proPlan.features.map((feature) => (
                    <div
                      key={feature}
                      className="flex items-start gap-2 text-sm font-light"
                    >
                      <span className="mt-1.5 size-1 shrink-0 rounded-full bg-primary" />
                      <PlanFeature feature={feature} />
                    </div>
                  ))}
                </div>
              </div>
            )}

            {isConfirming ? (
              <CheckoutConfirming isLate={checkoutPhase === "timeout"} />
            ) : (
              <RaisedButton
                className="w-full text-black!"
                color="#00bbff"
                onClick={handleSubscribe}
                disabled={!isCheckoutSettled(checkoutPhase)}
              >
                {isCheckoutSettled(checkoutPhase)
                  ? copy.subscribeCta
                  : "Opening checkout..."}
              </RaisedButton>
            )}

            <Button
              variant="light"
              size="sm"
              className="mx-auto mt-1 h-auto min-w-0 p-0 text-xs text-zinc-500 data-[hover=true]:bg-transparent data-[hover=true]:text-zinc-300 data-[hover=true]:underline"
              onPress={() => logout()}
            >
              Log out
            </Button>
          </ModalBody>
        )}
      </ModalContent>
    </Modal>
  );
}
