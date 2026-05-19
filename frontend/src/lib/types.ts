export type Role = "employee" | "manager" | "admin";

export type User = {
  id: string;
  email: string;
  name: string;
  role: Role;
  active: boolean;
  default_hourly_rate_cents: number | null;
};

export type TokensResponse = {
  access_token: string;
  refresh_token: string;
  user: User;
};

export type Client = {
  id: string;
  name: string;
  email: string | null;
  billing_address: string | null;
  currency: string;
  notes: string | null;
};

export type Project = {
  id: string;
  client_id: string;
  name: string;
  billable: boolean;
  default_rate_cents: number | null;
  rounding_minutes: number;
  active: boolean;
};

export type ProjectMember = {
  project_id: string;
  user_id: string;
  rate_override_cents: number | null;
};

export type EntryStatus = "draft" | "submitted" | "approved" | "invoiced";

export type TimeEntry = {
  id: string;
  user_id: string;
  project_id: string;
  description: string;
  started_at: string;
  ended_at: string | null;
  duration_seconds: number;
  status: EntryStatus;
  approved_by: string | null;
  approved_at: string | null;
  invoice_id: string | null;
  notes: string | null;
};

export type RunningTimer = {
  entry: TimeEntry;
  elapsed_seconds: number;
  state: "running" | "paused";
};

export type InvoiceStatus = "draft" | "sent" | "paid" | "void";

export type Invoice = {
  id: string;
  client_id: string;
  invoice_number: string;
  issue_date: string;
  due_date: string;
  status: InvoiceStatus;
  subtotal_cents: number;
  tax_rate: number;
  total_cents: number;
  notes: string | null;
  pdf_path: string | null;
};

export type InvoiceLine = {
  id: string;
  invoice_id: string;
  time_entry_id: string | null;
  description: string;
  quantity: number;
  unit_price_cents: number;
  amount_cents: number;
};
