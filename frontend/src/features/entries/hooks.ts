import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api } from "@/lib/api";
import type { ApiError } from "@/lib/api";
import { queryKeys } from "@/lib/queryKeys";
import type { TimeEntry } from "@/lib/types";

type EntryList = { entries: TimeEntry[] };

export function useEntries(params?: { start?: string; end?: string; status?: string }) {
  return useQuery<TimeEntry[]>({
    queryKey: queryKeys.entries(params),
    queryFn: async () =>
      (await api.get<EntryList>("/entries", params)).entries,
  });
}

export type CreateEntryInput = {
  project_id: string;
  started_at: string;
  ended_at: string;
  description?: string;
};

export function useCreateEntry() {
  const qc = useQueryClient();
  return useMutation<TimeEntry, ApiError, CreateEntryInput>({
    mutationFn: (input) => api.post<TimeEntry>("/entries", input),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: ["entries"] });
    },
  });
}

export function useDeleteEntry() {
  const qc = useQueryClient();
  return useMutation<unknown, ApiError, string>({
    mutationFn: (id) => api.delete<unknown>(`/entries/${id}`),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: ["entries"] });
    },
  });
}

export function useSubmitEntries() {
  const qc = useQueryClient();
  return useMutation<unknown, ApiError, string[]>({
    mutationFn: (ids) => api.post("/entries/bulk-submit", { entry_ids: ids }),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: ["entries"] });
    },
  });
}
