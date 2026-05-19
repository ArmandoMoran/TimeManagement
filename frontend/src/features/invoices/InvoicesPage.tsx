import { useState } from "react";

import { useClients } from "@/features/clients/hooks";
import { formatCents } from "@/lib/format";
import type { Invoice } from "@/lib/types";

import {
  useCreateInvoice,
  useInvoices,
  useMarkPaid,
  useMarkSent,
  usePreviewInvoice,
  useVoidInvoice,
  type PreviewResult,
} from "./hooks";

const STATUS_BADGE: Record<Invoice["status"], string> = {
  draft: "bg-gray-200 text-gray-700",
  sent: "bg-blue-100 text-blue-800",
  paid: "bg-green-100 text-green-800",
  void: "bg-red-100 text-red-800",
};

function isoToday(): string {
  return new Date().toISOString().slice(0, 10);
}

function isoDaysAgo(days: number): string {
  const d = new Date();
  d.setDate(d.getDate() - days);
  return d.toISOString().slice(0, 10);
}

export function InvoicesPage(): React.ReactElement {
  const { data: clients = [] } = useClients();
  const { data: invoices = [] } = useInvoices();
  const previewMutation = usePreviewInvoice();
  const createMutation = useCreateInvoice();
  const markSent = useMarkSent();
  const markPaid = useMarkPaid();
  const voidInvoice = useVoidInvoice();

  const [clientId, setClientId] = useState<string>("");
  const [start, setStart] = useState<string>(isoDaysAgo(14));
  const [end, setEnd] = useState<string>(isoToday());
  const [previewData, setPreviewData] = useState<PreviewResult | null>(null);

  function handlePreview(event: React.SyntheticEvent<HTMLFormElement>): void {
    event.preventDefault();
    if (!clientId) return;
    previewMutation.mutate(
      { client_id: clientId, start, end },
      {
        onSuccess: (data) => {
          setPreviewData(data);
        },
      },
    );
  }

  function handleCreate(): void {
    if (!clientId) return;
    createMutation.mutate(
      { client_id: clientId, start, end },
      {
        onSuccess: () => {
          setPreviewData(null);
        },
      },
    );
  }

  return (
    <section aria-labelledby="invoices-heading" className="space-y-6">
      <h2 id="invoices-heading" className="text-2xl font-semibold">
        Invoices
      </h2>

      <form
        onSubmit={handlePreview}
        aria-label="New invoice"
        className="space-y-3 rounded-md border p-4"
      >
        <h3 className="text-lg font-semibold">New invoice</h3>
        <div className="flex flex-wrap items-end gap-3">
          <div className="space-y-1">
            <label htmlFor="invoice-client" className="block text-xs font-medium">
              Client
            </label>
            <select
              id="invoice-client"
              value={clientId}
              onChange={(event) => {
                setClientId(event.target.value);
              }}
              className="rounded-md border px-3 py-2 text-sm"
              required
            >
              <option value="">Select…</option>
              {clients.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name}
                </option>
              ))}
            </select>
          </div>
          <div className="space-y-1">
            <label htmlFor="invoice-start" className="block text-xs font-medium">
              From
            </label>
            <input
              id="invoice-start"
              type="date"
              value={start}
              onChange={(event) => {
                setStart(event.target.value);
              }}
              className="rounded-md border px-3 py-2 text-sm"
            />
          </div>
          <div className="space-y-1">
            <label htmlFor="invoice-end" className="block text-xs font-medium">
              To
            </label>
            <input
              id="invoice-end"
              type="date"
              value={end}
              onChange={(event) => {
                setEnd(event.target.value);
              }}
              className="rounded-md border px-3 py-2 text-sm"
            />
          </div>
          <button
            type="submit"
            disabled={previewMutation.isPending}
            className="rounded-md border px-3 py-2 text-sm"
          >
            {previewMutation.isPending ? "Previewing…" : "Preview"}
          </button>
        </div>

        {previewMutation.isError && (
          <p role="alert" className="text-sm text-red-600">
            {previewMutation.error.message}
          </p>
        )}

        {previewData && (
          <div role="region" aria-label="Invoice preview" className="space-y-2 rounded-md bg-muted/30 p-3">
            <p className="text-sm font-medium">
              Preview for {previewData.client_name}
            </p>
            {previewData.lines.length === 0 ? (
              <p className="text-sm text-muted-foreground">
                No eligible approved entries in this range.
              </p>
            ) : (
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b text-left">
                    <th className="py-1 pr-3">Description</th>
                    <th className="py-1 pr-3">Hours</th>
                    <th className="py-1 pr-3">Rate</th>
                    <th className="py-1 pr-3 text-right">Amount</th>
                  </tr>
                </thead>
                <tbody>
                  {previewData.lines.map((line, i) => (
                    <tr key={i} className="border-b last:border-0">
                      <td className="py-1 pr-3">{line.description}</td>
                      <td className="py-1 pr-3">{line.hours.toFixed(2)}</td>
                      <td className="py-1 pr-3">
                        {formatCents(line.unit_price_cents, previewData.currency)}
                      </td>
                      <td className="py-1 pr-3 text-right">
                        {formatCents(line.amount_cents, previewData.currency)}
                      </td>
                    </tr>
                  ))}
                </tbody>
                <tfoot>
                  <tr className="font-medium">
                    <td colSpan={3} className="py-2">
                      Subtotal
                    </td>
                    <td className="py-2 text-right">
                      {formatCents(previewData.subtotal_cents, previewData.currency)}
                    </td>
                  </tr>
                </tfoot>
              </table>
            )}
            <button
              type="button"
              onClick={handleCreate}
              disabled={createMutation.isPending || previewData.lines.length === 0}
              className="rounded-md bg-primary px-3 py-2 text-sm font-medium text-primary-foreground disabled:opacity-50"
            >
              {createMutation.isPending ? "Creating…" : "Create invoice"}
            </button>
            {createMutation.isError && (
              <p role="alert" className="text-sm text-red-600">
                {createMutation.error.message}
              </p>
            )}
          </div>
        )}
      </form>

      <table className="w-full text-sm">
        <thead>
          <tr className="border-b text-left">
            <th className="py-2 pr-4 font-medium">Number</th>
            <th className="py-2 pr-4 font-medium">Issue date</th>
            <th className="py-2 pr-4 font-medium">Total</th>
            <th className="py-2 pr-4 font-medium">Status</th>
            <th className="py-2 pr-4 font-medium">Actions</th>
          </tr>
        </thead>
        <tbody>
          {invoices.map((invoice) => (
            <tr key={invoice.id} className="border-b last:border-0">
              <td className="py-2 pr-4 font-mono">{invoice.invoice_number}</td>
              <td className="py-2 pr-4">{invoice.issue_date}</td>
              <td className="py-2 pr-4">{formatCents(invoice.total_cents)}</td>
              <td className="py-2 pr-4">
                <span
                  className={`rounded-full px-2 py-0.5 text-xs ${STATUS_BADGE[invoice.status]}`}
                >
                  {invoice.status}
                </span>
              </td>
              <td className="py-2 pr-4 space-x-1">
                <a
                  href={`/api/v1/invoices/${invoice.id}/pdf`}
                  className="rounded border px-2 py-1 text-xs"
                  download
                >
                  PDF
                </a>
                {invoice.status === "draft" && (
                  <button
                    type="button"
                    className="rounded border px-2 py-1 text-xs"
                    onClick={() => {
                      markSent.mutate(invoice.id);
                    }}
                  >
                    Mark sent
                  </button>
                )}
                {(invoice.status === "draft" || invoice.status === "sent") && (
                  <button
                    type="button"
                    className="rounded border px-2 py-1 text-xs"
                    onClick={() => {
                      markPaid.mutate(invoice.id);
                    }}
                  >
                    Mark paid
                  </button>
                )}
                {invoice.status !== "paid" && invoice.status !== "void" && (
                  <button
                    type="button"
                    className="rounded border px-2 py-1 text-xs text-red-600"
                    onClick={() => {
                      voidInvoice.mutate(invoice.id);
                    }}
                  >
                    Void
                  </button>
                )}
              </td>
            </tr>
          ))}
          {invoices.length === 0 && (
            <tr>
              <td colSpan={5} className="py-2 text-muted-foreground">
                No invoices yet.
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </section>
  );
}
