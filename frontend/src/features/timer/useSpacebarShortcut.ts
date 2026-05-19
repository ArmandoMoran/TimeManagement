import { useEffect } from "react";

import {
  useCurrentTimer,
  useStartTimer,
  useStopTimer,
} from "./hooks";

function isEditableTarget(target: EventTarget | null): boolean {
  if (!(target instanceof HTMLElement)) return false;
  if (target.isContentEditable) return true;
  const tag = target.tagName;
  return tag === "INPUT" || tag === "TEXTAREA" || tag === "SELECT";
}

/**
 * Spacebar starts (when no active timer + default project picked) OR stops the
 * active timer. Ignored while an input/textarea/select/contenteditable element
 * has focus so it doesn't fight with typing.
 */
export function useSpacebarShortcut(options: {
  defaultProjectId?: string | null;
}): void {
  const { data: current } = useCurrentTimer();
  const start = useStartTimer();
  const stop = useStopTimer();

  useEffect(() => {
    function onKeyDown(event: KeyboardEvent): void {
      if (event.code !== "Space" && event.key !== " ") return;
      if (isEditableTarget(event.target)) return;
      event.preventDefault();
      if (current) {
        stop.mutate();
      } else if (options.defaultProjectId) {
        start.mutate({ project_id: options.defaultProjectId });
      }
    }
    window.addEventListener("keydown", onKeyDown);
    return () => {
      window.removeEventListener("keydown", onKeyDown);
    };
  }, [current, start, stop, options.defaultProjectId]);
}
