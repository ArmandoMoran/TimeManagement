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
      <header className="flex items-center justify-between border-b px-6 py-3">
        <h1 className="text-xl font-semibold tracking-tight">TimeTrack</h1>
        {isAuthenticated && (
          <div className="flex items-center gap-3 text-sm">
            <span aria-label="signed in as">{user?.name}</span>
            <button
              type="button"
              onClick={handleLogout}
              className="rounded-md border px-3 py-1 text-sm"
            >
              Log out
            </button>
          </div>
        )}
      </header>

      {isAuthenticated ? (
        <>
          <div className="flex">
            <nav className="w-48 border-r p-4" aria-label="Main">
              <ul className="space-y-1 text-sm">
                {visibleNav.map((item) => (
                  <li key={item.to}>
                    <Link
                      to={item.to}
                      className="block rounded px-2 py-1 hover:bg-muted"
                      activeProps={{
                        className: "block rounded px-2 py-1 bg-muted font-medium",
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
