// Centralized TanStack Query key factory. Reference these instead of typing
// strings in component code so a single rename propagates everywhere.
export const queryKeys = {
  me: ["auth", "me"] as const,
  clients: () => ["clients"] as const,
  client: (id: string) => ["clients", id] as const,
  projects: () => ["projects"] as const,
  project: (id: string) => ["projects", id] as const,
  entries: (params?: Record<string, string | undefined>) =>
    ["entries", params ?? {}] as const,
  timerCurrent: ["timer", "current"] as const,
  approvals: (params?: Record<string, string | undefined>) =>
    ["approvals", params ?? {}] as const,
  invoices: ["invoices"] as const,
  invoice: (id: string) => ["invoices", id] as const,
  reports: {
    utilization: (params: Record<string, string | undefined>) =>
      ["reports", "utilization", params] as const,
    revenue: (params: Record<string, string | undefined>) =>
      ["reports", "revenue", params] as const,
    outstanding: ["reports", "outstanding"] as const,
  },
} as const;
