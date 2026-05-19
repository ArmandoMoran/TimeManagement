import {
  createRootRoute,
  createRoute,
  createRouter,
  Navigate,
  redirect,
} from "@tanstack/react-router";
import { AppShell } from "@/components/AppShell";
import { ApprovalsPage } from "@/features/approvals/ApprovalsPage";
import { ClientsPage } from "@/features/clients/ClientsPage";
import { InvoicesPage } from "@/features/invoices/InvoicesPage";
import { LoginPage } from "@/features/auth/LoginPage";
import { ProjectsPage } from "@/features/projects/ProjectsPage";
import { ReportsPage } from "@/features/reports/ReportsPage";
import { TimesheetView } from "@/features/timesheet/TimesheetView";
import { TodayView } from "@/features/today/TodayView";
import { tokenStore } from "@/lib/tokenStore";

function requireAuth(): void {
  if (!tokenStore.getAccessToken()) {
    // TanStack Router uses thrown redirects as control flow.
    // eslint-disable-next-line @typescript-eslint/only-throw-error
    throw redirect({ to: "/login" });
  }
}

const rootRoute = createRootRoute({
  component: AppShell,
});

const loginRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "/login",
  component: LoginPage,
});

const indexRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "/",
  beforeLoad: requireAuth,
  component: TodayView,
});

const clientsRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "/clients",
  beforeLoad: requireAuth,
  component: ClientsPage,
});

const projectsRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "/projects",
  beforeLoad: requireAuth,
  component: ProjectsPage,
});

const timesheetRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "/timesheet",
  beforeLoad: requireAuth,
  component: TimesheetView,
});

const approvalsRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "/approvals",
  beforeLoad: requireAuth,
  component: ApprovalsPage,
});

const invoicesRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "/invoices",
  beforeLoad: requireAuth,
  component: InvoicesPage,
});

const reportsRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "/reports",
  beforeLoad: requireAuth,
  component: ReportsPage,
});

const protectedPlaceholders = ["/settings"] as const;

const placeholderRoutes = protectedPlaceholders.map((path) =>
  createRoute({
    getParentRoute: () => rootRoute,
    path,
    beforeLoad: requireAuth,
    component: () => (
      <section>
        <h2 className="text-2xl font-semibold capitalize">{path.slice(1)}</h2>
        <p className="mt-2 text-sm text-muted-foreground">Built out in a later phase.</p>
      </section>
    ),
  }),
);

const catchAllRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "*",
  component: () => <Navigate to="/" />,
});

const routeTree = rootRoute.addChildren([
  indexRoute,
  loginRoute,
  clientsRoute,
  projectsRoute,
  timesheetRoute,
  approvalsRoute,
  invoicesRoute,
  reportsRoute,
  ...placeholderRoutes,
  catchAllRoute,
]);

export const router = createRouter({
  routeTree,
  defaultPreload: "intent",
});

declare module "@tanstack/react-router" {
  interface Register {
    router: typeof router;
  }
}
