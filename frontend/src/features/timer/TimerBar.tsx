import { useEffect, useState } from "react";

import { formatHMS } from "@/lib/format";

import { usePauseTimer, useResumeTimer, useStopTimer, useCurrentTimer } from "./hooks";

export function TimerBar(): React.ReactElement | null {
  const { data: current } = useCurrentTimer();
  const pause = usePauseTimer();
  const resume = useResumeTimer();
  const stop = useStopTimer();

  // Local tick so the displayed elapsed counts up between server refetches.
  const [localElapsed, setLocalElapsed] = useState<number>(0);

  useEffect(() => {
    if (!current) {
      setLocalElapsed(0);
      return;
    }
    setLocalElapsed(current.elapsed_seconds);
    if (current.state !== "running") return;
    const id = window.setInterval(() => {
      setLocalElapsed((s) => s + 1);
    }, 1000);
    return () => {
      window.clearInterval(id);
    };
  }, [current]);

  if (!current) return null;

  return (
    <div
      role="status"
      aria-label="Active timer"
      className="flex items-center gap-3 border-t bg-muted/30 px-6 py-2 text-sm"
    >
      <span className="font-mono tabular-nums" data-testid="timer-elapsed">
        {formatHMS(localElapsed)}
      </span>
      <span className="text-muted-foreground">
        {current.entry.description || "(no description)"}
      </span>
      <div className="ml-auto flex gap-2">
        {current.state === "running" ? (
          <button
            type="button"
            className="rounded-md border px-3 py-1"
            onClick={() => {
              pause.mutate();
            }}
          >
            Pause
          </button>
        ) : (
          <button
            type="button"
            className="rounded-md border px-3 py-1"
            onClick={() => {
              resume.mutate();
            }}
          >
            Resume
          </button>
        )}
        <button
          type="button"
          className="rounded-md border bg-foreground px-3 py-1 text-background"
          onClick={() => {
            stop.mutate();
          }}
        >
          Stop
        </button>
      </div>
    </div>
  );
}
