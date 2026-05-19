import { useCurrentTimer, useStopTimer } from "./hooks";
import { useIdleDetection } from "./useIdleDetection";

/**
 * Renders an idle prompt when the user has been inactive while a timer ran.
 * "Keep" dismisses the prompt and continues tracking; "Discard" stops the
 * timer and lets the user fix the entry from Today afterwards.
 */
export function IdleModal(): React.ReactElement | null {
  const { shouldPrompt, dismiss } = useIdleDetection();
  const { data: current } = useCurrentTimer();
  const stop = useStopTimer();

  if (!shouldPrompt || !current) return null;

  function handleKeep(): void {
    dismiss();
  }

  function handleDiscard(): void {
    stop.mutate(undefined, { onSuccess: dismiss });
  }

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="idle-modal-title"
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/40"
    >
      <div className="w-full max-w-sm rounded-lg bg-background p-6 shadow-xl">
        <h2 id="idle-modal-title" className="text-lg font-semibold">
          You&rsquo;ve been idle
        </h2>
        <p className="mt-2 text-sm text-muted-foreground">
          The timer is still running. Keep this time, or stop and trim later?
        </p>
        <div className="mt-4 flex justify-end gap-2">
          <button
            type="button"
            onClick={handleDiscard}
            className="rounded-md border px-3 py-1.5 text-sm"
          >
            Stop timer
          </button>
          <button
            type="button"
            onClick={handleKeep}
            className="rounded-md bg-foreground px-3 py-1.5 text-sm font-medium text-background"
          >
            Keep going
          </button>
        </div>
      </div>
    </div>
  );
}
