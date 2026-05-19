import { useMemo, useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { formatCents, formatDuration } from "@/lib/format";

import { useOutstanding, useRevenue, useUtilization } from "./hooks";

function isoToday(): string {
  return new Date().toISOString().slice(0, 10);
}

function isoDaysAgo(days: number): string {
  const d = new Date();
  d.setDate(d.getDate() - days);
  return d.toISOString().slice(0, 10);
}

export function ReportsPage(): React.ReactElement {
  const [start, setStart] = useState<string>(isoDaysAgo(30));
  const [end, setEnd] = useState<string>(isoToday());

  const utilization = useUtilization({ start, end });
  const revenue = useRevenue({ start, end });
  const outstanding = useOutstanding();

  const utilizationData = useMemo(
    () =>
      (utilization.data ?? []).map((row) => ({
        name: row.user_name,
        billable: Math.round(row.billable_seconds / 3600),
        nonbillable: Math.round(
          (row.total_seconds - row.billable_seconds) / 3600,
        ),
        utilization: Math.round(row.utilization * 100),
      })),
    [utilization.data],
  );

  const revenueData = useMemo(
    () =>
      (revenue.data ?? []).map((row) => ({
        name: row.client_name,
        invoiced: row.invoiced_cents / 100,
        paid: row.paid_cents / 100,
      })),
    [revenue.data],
  );

  return (
    <section aria-labelledby="reports-heading" className="space-y-6">
      <header className="flex flex-wrap items-center gap-3">
        <h2 id="reports-heading" className="text-2xl font-semibold">
          Reports
        </h2>
        <div className="flex items-end gap-2 text-sm">
          <label className="space-y-1">
            <span className="block text-xs font-medium">From</span>
            <input
              type="date"
              value={start}
              onChange={(event) => {
                setStart(event.target.value);
              }}
              className="rounded-md border px-2 py-1"
            />
          </label>
          <label className="space-y-1">
            <span className="block text-xs font-medium">To</span>
            <input
              type="date"
              value={end}
              onChange={(event) => {
                setEnd(event.target.value);
              }}
              className="rounded-md border px-2 py-1"
            />
          </label>
        </div>
      </header>

      <div
        role="region"
        aria-label="Outstanding time"
        className="rounded-md border p-4"
      >
        <h3 className="text-lg font-semibold">Outstanding time</h3>
        <p className="mt-2 text-sm">
          Approved but uninvoiced:{" "}
          <span className="font-medium">
            {outstanding.data?.approved_uninvoiced_count ?? 0}
          </span>{" "}
          entries •{" "}
          <span className="font-medium" data-testid="outstanding-seconds">
            {formatDuration(outstanding.data?.approved_uninvoiced_seconds ?? 0)}
          </span>
        </p>
      </div>

      <div
        role="region"
        aria-label="Utilization"
        className="space-y-2 rounded-md border p-4"
      >
        <h3 className="text-lg font-semibold">Utilization by user</h3>
        {utilizationData.length === 0 ? (
          <p className="text-sm text-muted-foreground">No entries in this range.</p>
        ) : (
          <div style={{ width: "100%", height: 240 }}>
            <ResponsiveContainer>
              <BarChart data={utilizationData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis
                  label={{ value: "Hours", angle: -90, position: "insideLeft" }}
                />
                <Tooltip />
                <Bar dataKey="billable" stackId="hours" fill="#16a34a" />
                <Bar dataKey="nonbillable" stackId="hours" fill="#94a3b8" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        )}
      </div>

      <div
        role="region"
        aria-label="Revenue by client"
        className="space-y-2 rounded-md border p-4"
      >
        <h3 className="text-lg font-semibold">Revenue by client</h3>
        {revenueData.length === 0 ? (
          <p className="text-sm text-muted-foreground">No invoices in this range.</p>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b text-left">
                <th className="py-2 pr-4 font-medium">Client</th>
                <th className="py-2 pr-4 text-right font-medium">Invoiced</th>
                <th className="py-2 pr-4 text-right font-medium">Paid</th>
                <th className="py-2 pr-4 text-right font-medium">Outstanding</th>
              </tr>
            </thead>
            <tbody>
              {(revenue.data ?? []).map((row) => (
                <tr key={row.client_id} className="border-b last:border-0">
                  <td className="py-2 pr-4">{row.client_name}</td>
                  <td className="py-2 pr-4 text-right">
                    {formatCents(row.invoiced_cents)}
                  </td>
                  <td className="py-2 pr-4 text-right">
                    {formatCents(row.paid_cents)}
                  </td>
                  <td className="py-2 pr-4 text-right">
                    {formatCents(row.outstanding_cents)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </section>
  );
}
