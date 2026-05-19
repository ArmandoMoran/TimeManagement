import { useEffect, useState } from "react";

import { useCurrentTimer } from "./hooks";

const IDLE_AFTER_MS = 10 * 60 * 1000; // 10 minutes
const ACTIVITY_EVENTS = ["mousemove", "keydown", "click", "scroll", "touchstart"];

/**
 * Returns ``true`` whenever the user has been idle for ``IDLE_AFTER_MS`` while a
 * timer is running. Reset by any mouse/keyboard activity. The consuming
 * component decides what to do (typically show a modal).
 */
export function useIdleDetection(): {
  shouldPrompt: boolean;
  dismiss: () => void;
} {
  const { data: current } = useCurrentTimer();
  const [shouldPrompt, setShouldPrompt] = useState<boolean>(false);

  useEffect(() => {
    if (!current || current.state !== "running") {
      setShouldPrompt(false);
      return;
    }

    let timeoutId: number | undefined;

    function arm(): void {
      window.clearTimeout(timeoutId);
      timeoutId = window.setTimeout(() => {
        setShouldPrompt(true);
      }, IDLE_AFTER_MS);
    }

    function bumpActivity(): void {
      if (shouldPrompt) return; // wait for user dismiss
      arm();
    }

    arm();
    for (const event of ACTIVITY_EVENTS) {
      window.addEventListener(event, bumpActivity, { passive: true });
    }
    return () => {
      window.clearTimeout(timeoutId);
      for (const event of ACTIVITY_EVENTS) {
        window.removeEventListener(event, bumpActivity);
      }
    };
  }, [current, shouldPrompt]);

  return {
    shouldPrompt,
    dismiss: () => {
      setShouldPrompt(false);
    },
  };
}
