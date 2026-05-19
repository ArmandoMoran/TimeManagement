import { useState } from "react";

import { useProjects } from "@/features/projects/hooks";
import { formatDuration } from "@/lib/format";

import { useApprove, usePendingApprovals, useReject } from "./hooks";

export function ApprovalsPage(): React.ReactElement {
  const { data: pending = [] } = usePendingApprovals();
  const { data: projects = [] } = useProjects();
  const approve = useApprove();
  const reject = useReject();

  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [reason, setReason] = useState<string>("");

  function toggle(id: string): void {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }

  function selectAll(): void {
    setSelectedIds(new Set(pending.map((e) => e.id)));
  }

  function clearSelection(): void {
    setSelectedIds(new Set());
  }

  function handleApprove(): void {
    if (selectedIds.size === 0) return;
    approve.mutate([...selectedIds], { onSuccess: clearSelection });
  }

  function handleReject(): void {
    if (selectedIds.size === 0 || !reason.trim()) return;
    reject.mutate(
      { entry_ids: [...selectedIds], reason: reason.trim() },
      {
        onSuccess: () => {
          clearSelection();
          setReason("");
        },
      },
    );
  }

  return (
    <section aria-labelledby="approvals-heading" className="space-y-4">
      <h2 id="approvals-heading" className="text-2xl font-semibold">
        Approvals
      </h2>

      <div className="flex flex-wrap items-center gap-3 rounded-md border p-3">
        <button
          type="button"
          className="rounded-md border px-3 py-1 text-sm"
          onClick={selectAll}
          disabled={pending.length === 0}
        >
          Select all
        </button>
        <button
          type="button"
          className="rounded-md border px-3 py-1 text-sm"
          onClick={clearSelection}
          disabled={selectedIds.size === 0}
        >
          Clear
        </button>
        <span className="text-sm text-muted-foreground">
          {selectedIds.size} selected
        </span>
        <div className="ml-auto flex gap-2">
          <button
            type="button"
            className="rounded-md bg-green-700 px-3 py-1 text-sm text-white disabled:opacity-50"
            onClick={handleApprove}
            disabled={approve.isPending || selectedIds.size === 0}
          >
            {approve.isPending ? "Approving…" : "Approve selected"}
          </button>
          <input
            aria-label="Rejection reason"
            value={reason}
            onChange={(event) => {
              setReason(event.target.value);
            }}
            placeholder="Rejection reason"
            className="rounded-md border px-2 py-1 text-sm"
          />
          <button
            type="button"
            className="rounded-md bg-red-700 px-3 py-1 text-sm text-white disabled:opacity-50"
            onClick={handleReject}
            disabled={
              reject.isPending || selectedIds.size === 0 || !reason.trim()
            }
          >
            {reject.isPending ? "Rejecting…" : "Reject selected"}
          </button>
        </div>
      </div>

      <table className="w-full text-sm">
        <thead>
          <tr className="border-b text-left">
            <th className="py-2 pr-2" />
            <th className="py-2 pr-4 font-medium">Project</th>
            <th className="py-2 pr-4 font-medium">Description</th>
            <th className="py-2 pr-4 font-medium">Duration</th>
            <th className="py-2 pr-4 font-medium">User</th>
          </tr>
        </thead>
        <tbody>
          {pending.map((entry) => {
            const project = projects.find((p) => p.id === entry.project_id);
            return (
              <tr key={entry.id} className="border-b last:border-0">
                <td className="py-2 pr-2">
                  <input
                    type="checkbox"
                    aria-label={`Select entry ${entry.id}`}
                    checked={selectedIds.has(entry.id)}
                    onChange={() => {
                      toggle(entry.id);
                    }}
                  />
                </td>
                <td className="py-2 pr-4">{project?.name ?? "—"}</td>
                <td className="py-2 pr-4">{entry.description || "—"}</td>
                <td className="py-2 pr-4">
                  {formatDuration(entry.duration_seconds)}
                </td>
                <td className="py-2 pr-4 font-mono text-xs">{entry.user_id}</td>
              </tr>
            );
          })}
          {pending.length === 0 && (
            <tr>
              <td colSpan={5} className="py-2 text-muted-foreground">
                Nothing waiting for approval.
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </section>
  );
}
