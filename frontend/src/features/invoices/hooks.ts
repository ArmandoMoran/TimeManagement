import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api } from "@/lib/api";
import type { ApiError } from "@/lib/api";
import { queryKeys } from "@/lib/queryKeys";
import type { Invoice } from "@/lib/types";

type InvoiceList = { invoices: Invoice[] };

export type PreviewLine = {
  description: string;
  hours: number;
  unit_price_cents: number;
  amount_cents: number;
};

export type PreviewResult = {
  client_id: string;
  client_name: string;
  currency: string;
  lines: PreviewLine[];
  subtotal_cents: number;
};

export function useInvoices() {
  return useQuery<Invoice[]>({
    queryKey: queryKeys.invoices,
    queryFn: async () => (await api.get<InvoiceList>("/invoices")).invoices,
  });
}

export type PreviewInput = {
  client_id: string;
  start: string;
  end: string;
};

export function usePreviewInvoice() {
  return useMutation<PreviewResult, ApiError, PreviewInput>({
    mutationFn: (input) => api.post<PreviewResult>("/invoices/preview", input),
  });
}

export type CreateInvoiceInput = {
  client_id: string;
  start: string;
  end: string;
  tax_rate?: number;
  due_in_days?: number;
};

export function useCreateInvoice() {
  const qc = useQueryClient();
  return useMutation<Invoice, ApiError, CreateInvoiceInput>({
    mutationFn: (input) => api.post<Invoice>("/invoices", input),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: queryKeys.invoices });
    },
  });
}

export function useMarkSent() {
  const qc = useQueryClient();
  return useMutation<Invoice, ApiError, string>({
    mutationFn: (id) => api.post<Invoice>(`/invoices/${id}/send`),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: queryKeys.invoices });
    },
  });
}

export function useMarkPaid() {
  const qc = useQueryClient();
  return useMutation<Invoice, ApiError, string>({
    mutationFn: (id) => api.post<Invoice>(`/invoices/${id}/mark-paid`),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: queryKeys.invoices });
    },
  });
}

export function useVoidInvoice() {
  const qc = useQueryClient();
  return useMutation<Invoice, ApiError, string>({
    mutationFn: (id) => api.post<Invoice>(`/invoices/${id}/void`),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: queryKeys.invoices });
    },
  });
}
