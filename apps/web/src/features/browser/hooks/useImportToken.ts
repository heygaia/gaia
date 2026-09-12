import { useMutation } from "@tanstack/react-query";
import { useCallback, useEffect, useState } from "react";
import { browserApi } from "../api/browserApi";

const COUNTDOWN_TICK_MS = 1000;

/** Mints the single-use `gaia-connect` code and counts down its life; call
 * `mint` again once it expires. */
export function useImportToken() {
  // The expiry instant is captured at mint time, not derived on render, so a
  // re-render never restarts the clock.
  const [expiresAt, setExpiresAt] = useState<number | null>(null);
  const [secondsLeft, setSecondsLeft] = useState(0);

  const mintMutation = useMutation({
    mutationFn: () => browserApi.mintImportToken(),
    onSuccess: (data) =>
      setExpiresAt(Date.now() + data.expires_in_seconds * 1000),
  });

  useEffect(() => {
    if (expiresAt === null) return undefined;
    const tick = () =>
      setSecondsLeft(Math.max(0, Math.ceil((expiresAt - Date.now()) / 1000)));
    tick();
    const id = setInterval(tick, COUNTDOWN_TICK_MS);
    return () => clearInterval(id);
  }, [expiresAt]);

  const { mutate, reset: resetMutation } = mintMutation;
  const mint = useCallback(() => mutate(), [mutate]);
  const reset = useCallback(() => {
    resetMutation();
    setExpiresAt(null);
    setSecondsLeft(0);
  }, [resetMutation]);

  return {
    token: mintMutation.data?.token ?? null,
    secondsLeft,
    isExpired: expiresAt !== null && secondsLeft <= 0,
    isMinting: mintMutation.isPending,
    error: mintMutation.error as Error | null,
    mint,
    reset,
  };
}
