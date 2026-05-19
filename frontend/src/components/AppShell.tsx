import { Link, Outlet, useNavigate, useRouter } from "@tanstack/react-router";

import { IdleModal } from "@/features/timer/IdleModal";
import { TimerBar } from "@/features/timer/TimerBar";
import { useCurrentUser, useLogout } from "@/features/auth/useAuth";

const NAV_ITEMS = [
  { to: "/", label: "Today" },
  { to: "/timesheet", label: "Timesheet" },
  { to: "/approvals", label: "Approvals", roles: ["manager", "admin"] as const },
  { to: "/clients", label: "Clients" },
  { to: "/projects", label: "Projects" },
  { to: "/invoices", label: "Invoices" },
  { to: "/reports", label: "Reports" },
  { to: "/settings", label: "Settings" },
];

export function AppShell(): React.ReactElement {
  const { user, isAuthenticated } = useCurrentUser();
  const { logout } = useLogout();
  const navigate = useNavigate();
  const router = useRouter();

  const visibleNav = NAV_ITEMS.filter((item) => {
    if (!item.roles) return true;
    return user ? item.roles.includes(user.role as never) : false;
  });

  function handleLogout(): void {
    void (async () => {
      await logout();
      await router.invalidate();
      await navigate({ to: "/login" });
    })();
  }

  return (
    <div className="min-h-screen bg-background text-foreground">
      <header className="flex items-center justify-between border-b border-border bg-card px-6 py-3 shadow-sm">
        <div className="flex items-center gap-2">
          <div
            aria-hidden
            className="h-6 w-6 rounded-md bg-primary"
            style={{
              backgroundImage:
                "linear-gradient(135deg, var(--color-primary) 0%, oklch(0.7 0.18 220) 100%)",
            }}
          />
          <h1 className="text-xl font-semibold tracking-tight text-primary">
            TimeTrack
          </h1>
        </div>
        {isAuthenticated && (
          <div className="flex items-center gap-3 text-sm">
            <span aria-label="signed in as" className="text-muted-foreground">
              {user?.name}
            </span>
            <button
              type="button"
              onClick={handleLogout}
              className="rounded-md border border-border bg-background px-3 py-1 text-sm hover:bg-muted"
            >
              Log out
            </button>
          </div>
        )}
      </header>

      {isAuthenticated ? (
        <>
          <div className="flex">
            <nav
              className="w-52 border-r border-border bg-card p-4"
              aria-label="Main"
            >
              <ul className="space-y-0.5 text-sm">
                {visibleNav.map((item) => (
                  <li key={item.to}>
                    <Link
                      to={item.to}
                      className="block rounded-md px-3 py-1.5 text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
                      activeProps={{
                        className:
                          "block rounded-md px-3 py-1.5 bg-accent text-accent-foreground font-medium",
                      }}
                    >
                      {item.label}
                    </Link>
                  </li>
                ))}
              </ul>
            </nav>
            <main className="flex-1 p-6">
              <Outlet />
            </main>
          </div>
          <TimerBar />
          <IdleModal />
        </>
      ) : (
        <main>
          <Outlet />
        </main>
      )}
    </div>
  );
}
