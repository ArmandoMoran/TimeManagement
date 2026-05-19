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

  const isRunning = current.state === "running";

  return (
    <div
      role="status"
      aria-label="Active timer"
      className="sticky bottom-0 flex items-center gap-3 border-t border-border bg-card px-6 py-2 text-sm shadow-[0_-1px_2px_rgba(0,0,0,0.04)]"
    >
      <span
        aria-hidden
        className={`h-2.5 w-2.5 rounded-full ${
          isRunning ? "bg-success animate-pulse" : "bg-warning"
        }`}
      />
      <span
        className="font-mono text-base font-semibold tabular-nums text-primary"
        data-testid="timer-elapsed"
      >
        {formatHMS(localElapsed)}
      </span>
      <span className="text-muted-foreground">
        {current.entry.description || "(no description)"}
      </span>
      <div className="ml-auto flex gap-2">
        {isRunning ? (
          <button
            type="button"
            className="rounded-md border border-border bg-background px-3 py-1 hover:bg-muted"
            onClick={() => {
              pause.mutate();
            }}
          >
            Pause
          </button>
        ) : (
          <button
            type="button"
            className="rounded-md border border-border bg-background px-3 py-1 hover:bg-muted"
            onClick={() => {
              resume.mutate();
            }}
          >
            Resume
          </button>
        )}
        <button
          type="button"
          className="rounded-md bg-primary px-3 py-1 text-primary-foreground hover:opacity-90"
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
