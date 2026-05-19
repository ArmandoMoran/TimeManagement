import { useQuery } from "@tanstack/react-query";

import { api } from "@/lib/api";
import { queryKeys } from "@/lib/queryKeys";

export type UtilizationRow = {
  user_id: string;
  user_name: string;
  total_seconds: number;
  billable_seconds: number;
  utilization: number;
};

export type RevenueRow = {
  client_id: string;
  client_name: string;
  invoiced_cents: number;
  paid_cents: number;
  outstanding_cents: number;
};

export function useUtilization(params: { start: string; end: string }) {
  return useQuery({
    queryKey: queryKeys.reports.utilization(params),
    queryFn: async () =>
      (
        await api.get<{ rows: UtilizationRow[]; start: string; end: string }>(
          "/reports/utilization",
          params,
        )
      ).rows,
  });
}

export function useRevenue(params: { start: string; end: string }) {
  return useQuery({
    queryKey: queryKeys.reports.revenue(params),
    queryFn: async () =>
      (
        await api.get<{ rows: RevenueRow[]; start: string; end: string }>(
          "/reports/revenue",
          params,
        )
      ).rows,
  });
}

export function useOutstanding() {
  return useQuery({
    queryKey: queryKeys.reports.outstanding,
    queryFn: () =>
      api.get<{ approved_uninvoiced_count: number; approved_uninvoiced_seconds: number }>(
        "/reports/outstanding",
      ),
  });
}
