import { addDays, endOfWeek, format, startOfWeek } from "date-fns";
import { useMemo, useState } from "react";

import { useEntries, useSubmitEntries } from "@/features/entries/hooks";
import { useProjects } from "@/features/projects/hooks";
import { formatDuration } from "@/lib/format";
import type { TimeEntry } from "@/lib/types";

const STATUS_BADGE: Record<TimeEntry["status"], string> = {
  draft: "bg-gray-200 text-gray-700",
  submitted: "bg-blue-100 text-blue-800",
  approved: "bg-green-100 text-green-800",
  invoiced: "bg-purple-100 text-purple-800",
};

function weekStart(date: Date): Date {
  return startOfWeek(date, { weekStartsOn: 1 });
}

export function TimesheetView(): React.ReactElement {
  const [anchor, setAnchor] = useState<Date>(() => new Date());
  const start = useMemo(() => weekStart(anchor), [anchor]);
  const end = useMemo(() => endOfWeek(anchor, { weekStartsOn: 1 }), [anchor]);
  const days = useMemo(
    () => Array.from({ length: 7 }, (_, i) => addDays(start, i)),
    [start],
  );

  const { data: projects = [] } = useProjects();
  const { data: entries = [] } = useEntries({
    start: start.toISOString(),
    end: end.toISOString(),
  });
  const submit = useSubmitEntries();

  // Build a project_id -> day_index -> seconds map.
  const grid = useMemo(() => {
    const map = new Map<string, number[]>();
    for (const entry of entries) {
      const projectId = entry.project_id;
      if (!map.has(projectId)) map.set(projectId, [0, 0, 0, 0, 0, 0, 0]);
      const date = new Date(entry.started_at);
      const dayOffset = Math.floor(
        (date.getTime() - start.getTime()) / (24 * 60 * 60 * 1000),
      );
      const row = map.get(projectId);
      if (row && dayOffset >= 0 && dayOffset < 7) {
        row[dayOffset] = (row[dayOffset] ?? 0) + entry.duration_seconds;
      }
    }
    return map;
  }, [entries, start]);

  const dayTotals = useMemo(() => {
    const totals = [0, 0, 0, 0, 0, 0, 0];
    for (const row of grid.values()) {
      row.forEach((s, i) => {
        totals[i] = (totals[i] ?? 0) + s;
      });
    }
    return totals;
  }, [grid]);

  const weekTotal = dayTotals.reduce((a, b) => a + b, 0);

  function handleSubmitWeek(): void {
    const draftIds = entries
      .filter((e) => e.status === "draft" && e.ended_at !== null)
      .map((e) => e.id);
    if (draftIds.length === 0) return;
    submit.mutate(draftIds);
  }

  return (
    <section aria-labelledby="timesheet-heading" className="space-y-6">
      <header className="flex flex-wrap items-center gap-3">
        <h2 id="timesheet-heading" className="text-2xl font-semibold">
          Timesheet
        </h2>
        <div className="flex items-center gap-2 text-sm">
          <button
            type="button"
            className="rounded-md border px-2 py-1"
            onClick={() => {
              setAnchor(addDays(anchor, -7));
            }}
          >
            ← Prev
          </button>
          <span className="font-medium" data-testid="week-range">
            {format(start, "MMM d")} – {format(end, "MMM d, yyyy")}
          </span>
          <button
            type="button"
            className="rounded-md border px-2 py-1"
            onClick={() => {
              setAnchor(addDays(anchor, 7));
            }}
          >
            Next →
          </button>
          <button
            type="button"
            className="rounded-md border px-2 py-1"
            onClick={() => {
              setAnchor(new Date());
            }}
          >
            This week
          </button>
        </div>
        <div className="ml-auto flex items-center gap-3 text-sm">
          <span>
            Week total: <span className="font-medium">{formatDuration(weekTotal)}</span>
          </span>
          <button
            type="button"
            disabled={submit.isPending}
            onClick={handleSubmitWeek}
            className="rounded-md bg-foreground px-3 py-1 text-sm font-medium text-background disabled:opacity-50"
          >
            {submit.isPending ? "Submitting…" : "Submit week"}
          </button>
        </div>
      </header>

      <table className="w-full text-sm">
        <thead>
          <tr className="border-b text-left">
            <th className="py-2 pr-4 font-medium">Project</th>
            {days.map((d) => (
              <th key={d.toISOString()} className="py-2 pr-2 text-center font-medium">
                {format(d, "EEE d")}
              </th>
            ))}
            <th className="py-2 pr-4 text-right font-medium">Total</th>
          </tr>
        </thead>
        <tbody>
          {Array.from(grid.entries()).map(([projectId, row]) => {
            const project = projects.find((p) => p.id === projectId);
            const rowTotal = row.reduce((a, b) => a + b, 0);
            return (
              <tr key={projectId} className="border-b last:border-0">
                <td className="py-2 pr-4">{project?.name ?? "—"}</td>
                {row.map((s, i) => (
                  <td
                    key={i}
                    className="py-2 pr-2 text-center font-mono tabular-nums"
                  >
                    {s > 0 ? formatDuration(s) : "—"}
                  </td>
                ))}
                <td className="py-2 pr-4 text-right font-medium">
                  {formatDuration(rowTotal)}
                </td>
              </tr>
            );
          })}
          {grid.size === 0 && (
            <tr>
              <td colSpan={9} className="py-4 text-center text-muted-foreground">
                No entries this week.
              </td>
            </tr>
          )}
        </tbody>
        <tfoot>
          <tr className="border-t font-medium">
            <td className="py-2 pr-4">Day total</td>
            {dayTotals.map((s, i) => (
              <td key={i} className="py-2 pr-2 text-center font-mono tabular-nums">
                {s > 0 ? formatDuration(s) : "—"}
              </td>
            ))}
            <td className="py-2 pr-4 text-right">{formatDuration(weekTotal)}</td>
          </tr>
        </tfoot>
      </table>

      <div>
        <h3 className="mb-2 text-lg font-semibold">Entries</h3>
        <ul className="space-y-1 text-sm">
          {entries.map((e) => {
            const project = projects.find((p) => p.id === e.project_id);
            return (
              <li
                key={e.id}
                className="flex items-center justify-between border-b py-1 last:border-0"
              >
                <span>
                  <span className="font-medium">{project?.name ?? "—"}</span>
                  {e.description && ` • ${e.description}`}
                </span>
                <span className="flex items-center gap-3 text-xs">
                  <span>{formatDuration(e.duration_seconds)}</span>
                  <span
                    className={`rounded-full px-2 py-0.5 ${STATUS_BADGE[e.status]}`}
                  >
                    {e.status}
                  </span>
                </span>
              </li>
            );
          })}
        </ul>
      </div>
    </section>
  );
}
