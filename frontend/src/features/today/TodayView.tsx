import { useMemo, useState } from "react";

import { useProjects } from "@/features/projects/hooks";
import {
  useCreateEntry,
  useDeleteEntry,
  useEntries,
  useSubmitEntries,
} from "@/features/entries/hooks";
import { useStartTimer, useCurrentTimer } from "@/features/timer/hooks";
import { useSpacebarShortcut } from "@/features/timer/useSpacebarShortcut";
import { formatDuration } from "@/lib/format";

function isoStartOfDay(): string {
  const now = new Date();
  now.setHours(0, 0, 0, 0);
  return now.toISOString();
}

function isoEndOfDay(): string {
  const now = new Date();
  now.setHours(23, 59, 59, 999);
  return now.toISOString();
}

export function TodayView(): React.ReactElement {
  const { data: projects = [] } = useProjects();
  const { data: current } = useCurrentTimer();
  const start = useStartTimer();
  const createManual = useCreateEntry();
  const deleteEntry = useDeleteEntry();
  const submit = useSubmitEntries();

  const entries = useEntries({ start: isoStartOfDay(), end: isoEndOfDay() });

  const [projectId, setProjectId] = useState<string>("");

  useSpacebarShortcut({ defaultProjectId: projectId || projects[0]?.id });
  const [description, setDescription] = useState<string>("");

  const dayTotal = useMemo(
    () =>
      (entries.data ?? []).reduce<number>(
        (sum, e) => sum + e.duration_seconds,
        0,
      ),
    [entries.data],
  );

  function onStart(event: React.SyntheticEvent<HTMLFormElement>): void {
    event.preventDefault();
    if (!projectId) return;
    start.mutate({ project_id: projectId, description: description.trim() });
    setDescription("");
  }

  const [manualStart, setManualStart] = useState<string>("");
  const [manualEnd, setManualEnd] = useState<string>("");
  const [manualDescription, setManualDescription] = useState<string>("");
  const [manualProjectId, setManualProjectId] = useState<string>("");

  function onAddManual(event: React.SyntheticEvent<HTMLFormElement>): void {
    event.preventDefault();
    if (!manualProjectId || !manualStart || !manualEnd) return;
    createManual.mutate(
      {
        project_id: manualProjectId,
        started_at: new Date(manualStart).toISOString(),
        ended_at: new Date(manualEnd).toISOString(),
        description: manualDescription.trim(),
      },
      {
        onSuccess: () => {
          setManualStart("");
          setManualEnd("");
          setManualDescription("");
        },
      },
    );
  }

  function onSubmitWeek(): void {
    const draftIds = (entries.data ?? [])
      .filter((e) => e.status === "draft" && e.ended_at !== null)
      .map((e) => e.id);
    if (draftIds.length === 0) return;
    submit.mutate(draftIds);
  }

  return (
    <section aria-labelledby="today-heading" className="space-y-6">
      <header className="flex items-center justify-between">
        <h2 id="today-heading" className="text-2xl font-semibold">
          Today
        </h2>
        <p className="text-sm text-muted-foreground">
          Day total: <span className="font-medium">{formatDuration(dayTotal)}</span>
        </p>
      </header>

      {!current && (
        <form
          onSubmit={onStart}
          aria-label="Start timer"
          className="flex flex-wrap items-end gap-3 rounded-md border p-4"
        >
          <div className="space-y-1">
            <label htmlFor="start-project" className="block text-xs font-medium">
              Project
            </label>
            <select
              id="start-project"
              value={projectId}
              onChange={(event) => {
                setProjectId(event.target.value);
              }}
              className="rounded-md border px-3 py-2 text-sm"
              required
            >
              <option value="">Select…</option>
              {projects.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name}
                </option>
              ))}
            </select>
          </div>
          <div className="space-y-1 flex-1 min-w-[200px]">
            <label htmlFor="start-description" className="block text-xs font-medium">
              What are you working on?
            </label>
            <input
              id="start-description"
              value={description}
              onChange={(event) => {
                setDescription(event.target.value);
              }}
              className="w-full rounded-md border px-3 py-2 text-sm"
            />
          </div>
          <button
            type="submit"
            disabled={start.isPending}
            className="rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground disabled:opacity-50"
          >
            {start.isPending ? "Starting…" : "Start timer"}
          </button>
        </form>
      )}

      <div className="space-y-3">
        <header className="flex items-center justify-between">
          <h3 className="text-lg font-semibold">Today&rsquo;s entries</h3>
          <button
            type="button"
            onClick={onSubmitWeek}
            disabled={submit.isPending}
            className="rounded-md border px-3 py-1 text-sm disabled:opacity-50"
          >
            Submit drafts
          </button>
        </header>

        <table className="w-full text-sm">
          <thead>
            <tr className="border-b text-left">
              <th className="py-2 pr-4 font-medium">Project</th>
              <th className="py-2 pr-4 font-medium">Description</th>
              <th className="py-2 pr-4 font-medium">Duration</th>
              <th className="py-2 pr-4 font-medium">Status</th>
              <th className="py-2 pr-4 font-medium" />
            </tr>
          </thead>
          <tbody>
            {(entries.data ?? []).map((e) => {
              const project = projects.find((p) => p.id === e.project_id);
              return (
                <tr key={e.id} className="border-b last:border-0">
                  <td className="py-2 pr-4">{project?.name ?? "—"}</td>
                  <td className="py-2 pr-4">{e.description || "—"}</td>
                  <td className="py-2 pr-4">
                    {e.ended_at ? formatDuration(e.duration_seconds) : "Running…"}
                  </td>
                  <td className="py-2 pr-4 capitalize">{e.status}</td>
                  <td className="py-2 pr-4">
                    {e.status === "draft" && e.ended_at && (
                      <button
                        type="button"
                        className="text-xs text-red-600"
                        onClick={() => {
                          deleteEntry.mutate(e.id);
                        }}
                      >
                        Delete
                      </button>
                    )}
                  </td>
                </tr>
              );
            })}
            {(entries.data ?? []).length === 0 && (
              <tr>
                <td colSpan={5} className="py-2 text-muted-foreground">
                  No entries yet today.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      <form
        onSubmit={onAddManual}
        aria-label="Add manual entry"
        className="space-y-3 rounded-md border p-4"
      >
        <h3 className="text-lg font-semibold">Add manual entry</h3>
        <div className="flex flex-wrap items-end gap-3">
          <div className="space-y-1">
            <label htmlFor="manual-project" className="block text-xs font-medium">
              Project
            </label>
            <select
              id="manual-project"
              value={manualProjectId}
              onChange={(event) => {
                setManualProjectId(event.target.value);
              }}
              className="rounded-md border px-3 py-2 text-sm"
              required
            >
              <option value="">Select…</option>
              {projects.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name}
                </option>
              ))}
            </select>
          </div>
          <div className="space-y-1">
            <label htmlFor="manual-start" className="block text-xs font-medium">
              Start
            </label>
            <input
              id="manual-start"
              type="datetime-local"
              value={manualStart}
              onChange={(event) => {
                setManualStart(event.target.value);
              }}
              className="rounded-md border px-3 py-2 text-sm"
              required
            />
          </div>
          <div className="space-y-1">
            <label htmlFor="manual-end" className="block text-xs font-medium">
              End
            </label>
            <input
              id="manual-end"
              type="datetime-local"
              value={manualEnd}
              onChange={(event) => {
                setManualEnd(event.target.value);
              }}
              className="rounded-md border px-3 py-2 text-sm"
              required
            />
          </div>
          <div className="space-y-1 flex-1 min-w-[200px]">
            <label htmlFor="manual-description" className="block text-xs font-medium">
              Description
            </label>
            <input
              id="manual-description"
              value={manualDescription}
              onChange={(event) => {
                setManualDescription(event.target.value);
              }}
              className="w-full rounded-md border px-3 py-2 text-sm"
            />
          </div>
          <button
            type="submit"
            disabled={createManual.isPending}
            className="rounded-md bg-primary px-3 py-2 text-sm font-medium text-primary-foreground disabled:opacity-50"
          >
            {createManual.isPending ? "Adding…" : "Add entry"}
          </button>
        </div>
      </form>
    </section>
  );
}
