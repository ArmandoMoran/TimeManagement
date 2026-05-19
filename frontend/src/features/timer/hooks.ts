import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api } from "@/lib/api";
import type { ApiError } from "@/lib/api";
import { queryKeys } from "@/lib/queryKeys";
import type { RunningTimer, TimeEntry } from "@/lib/types";

export function useCurrentTimer() {
  return useQuery<RunningTimer | null>({
    queryKey: queryKeys.timerCurrent,
    queryFn: async () => api.get<RunningTimer | null>("/timer/current"),
    refetchInterval: 30_000,
    refetchOnWindowFocus: true,
  });
}

function invalidateTimer(qc: ReturnType<typeof useQueryClient>): void {
  void qc.invalidateQueries({ queryKey: queryKeys.timerCurrent });
  void qc.invalidateQueries({ queryKey: ["entries"] });
}

export function useStartTimer() {
  const qc = useQueryClient();
  return useMutation<TimeEntry, ApiError, { project_id: string; description?: string }>(
    {
      mutationFn: (input) => api.post<TimeEntry>("/timer/start", input),
      onSuccess: () => {
        invalidateTimer(qc);
      },
    },
  );
}

export function usePauseTimer() {
  const qc = useQueryClient();
  return useMutation<TimeEntry, ApiError>({
    mutationFn: () => api.post<TimeEntry>("/timer/pause"),
    onSuccess: () => {
      invalidateTimer(qc);
    },
  });
}

export function useResumeTimer() {
  const qc = useQueryClient();
  return useMutation<TimeEntry, ApiError>({
    mutationFn: () => api.post<TimeEntry>("/timer/resume"),
    onSuccess: () => {
      invalidateTimer(qc);
    },
  });
}

export function useStopTimer() {
  const qc = useQueryClient();
  return useMutation<TimeEntry, ApiError>({
    mutationFn: () => api.post<TimeEntry>("/timer/stop"),
    onSuccess: () => {
      invalidateTimer(qc);
    },
  });
}
