import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api } from "@/lib/api";
import type { ApiError } from "@/lib/api";
import { queryKeys } from "@/lib/queryKeys";
import type { TimeEntry } from "@/lib/types";

type EntryList = { entries: TimeEntry[] };

export function usePendingApprovals() {
  return useQuery<TimeEntry[]>({
    queryKey: queryKeys.approvals(),
    queryFn: async () => (await api.get<EntryList>("/approvals")).entries,
  });
}

export function useApprove() {
  const qc = useQueryClient();
  return useMutation<unknown, ApiError, string[]>({
    mutationFn: (ids) => api.post("/approvals/approve", { entry_ids: ids }),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: queryKeys.approvals() });
      void qc.invalidateQueries({ queryKey: ["entries"] });
    },
  });
}

export function useReject() {
  const qc = useQueryClient();
  return useMutation<unknown, ApiError, { entry_ids: string[]; reason: string }>({
    mutationFn: (input) => api.post("/approvals/reject", input),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: queryKeys.approvals() });
      void qc.invalidateQueries({ queryKey: ["entries"] });
    },
  });
}
