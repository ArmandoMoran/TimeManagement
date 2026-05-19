import { useState } from "react";

import { useClients } from "@/features/clients/hooks";

import {
  useAddProjectMember,
  useCreateProject,
  useProjectMembers,
  useProjects,
} from "./hooks";

export function ProjectsPage(): React.ReactElement {
  const { data: clients = [] } = useClients();
  const { data: projects = [], isLoading } = useProjects();
  const create = useCreateProject();

  const [name, setName] = useState<string>("");
  const [clientId, setClientId] = useState<string>("");
  const [rateDollars, setRateDollars] = useState<string>("150");
  const [selectedProject, setSelectedProject] = useState<string | undefined>(undefined);

  function handleCreate(event: React.SyntheticEvent<HTMLFormElement>): void {
    event.preventDefault();
    if (!name.trim() || !clientId) return;
    const rate = Number(rateDollars);
    const rateCents = Number.isFinite(rate) && rate > 0 ? Math.round(rate * 100) : null;
    create.mutate(
      {
        client_id: clientId,
        name: name.trim(),
        default_rate_cents: rateCents,
      },
      {
        onSuccess: (project) => {
          setName("");
          setSelectedProject(project.id);
        },
      },
    );
  }

  return (
    <section aria-labelledby="projects-heading" className="space-y-6">
      <h2 id="projects-heading" className="text-2xl font-semibold">
        Projects
      </h2>

      <form onSubmit={handleCreate} className="flex flex-wrap items-end gap-3" aria-label="New project">
        <div className="space-y-1">
          <label htmlFor="project-client" className="block text-xs font-medium">
            Client
          </label>
          <select
            id="project-client"
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
          <label htmlFor="project-name" className="block text-xs font-medium">
            Name
          </label>
          <input
            id="project-name"
            value={name}
            onChange={(event) => {
              setName(event.target.value);
            }}
            className="rounded-md border px-3 py-2 text-sm"
            required
          />
        </div>
        <div className="space-y-1">
          <label htmlFor="project-rate" className="block text-xs font-medium">
            Rate ($/hr)
          </label>
          <input
            id="project-rate"
            type="number"
            min={0}
            value={rateDollars}
            onChange={(event) => {
              setRateDollars(event.target.value);
            }}
            className="w-24 rounded-md border px-3 py-2 text-sm"
          />
        </div>
        <button
          type="submit"
          disabled={create.isPending}
          className="rounded-md bg-foreground px-3 py-2 text-sm font-medium text-background disabled:opacity-50"
        >
          {create.isPending ? "Creating…" : "Create project"}
        </button>
        {create.isError && (
          <p role="alert" className="text-sm text-red-600">
            {create.error.message}
          </p>
        )}
      </form>

      {isLoading ? (
        <p>Loading…</p>
      ) : (
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b text-left">
              <th className="py-2 pr-4 font-medium">Name</th>
              <th className="py-2 pr-4 font-medium">Client</th>
              <th className="py-2 pr-4 font-medium">Rate</th>
              <th className="py-2 pr-4 font-medium">Members</th>
            </tr>
          </thead>
          <tbody>
            {projects.map((p) => {
              const client = clients.find((c) => c.id === p.client_id);
              const rate = p.default_rate_cents
                ? `$${(p.default_rate_cents / 100).toFixed(2)}/hr`
                : "—";
              return (
                <tr key={p.id} className="border-b last:border-0">
                  <td className="py-2 pr-4">{p.name}</td>
                  <td className="py-2 pr-4">{client?.name ?? "—"}</td>
                  <td className="py-2 pr-4">{rate}</td>
                  <td className="py-2 pr-4">
                    <button
                      type="button"
                      className="rounded-md border px-2 py-1 text-xs"
                      onClick={() => {
                        setSelectedProject(p.id);
                      }}
                    >
                      Manage
                    </button>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      )}

      {selectedProject && (
        <ProjectMembersPanel projectId={selectedProject} />
      )}
    </section>
  );
}

function ProjectMembersPanel({ projectId }: { projectId: string }): React.ReactElement {
  const { data: members = [] } = useProjectMembers(projectId);
  const add = useAddProjectMember(projectId);
  const [userId, setUserId] = useState<string>("");
  const [overrideDollars, setOverrideDollars] = useState<string>("");

  function handleAdd(event: React.SyntheticEvent<HTMLFormElement>): void {
    event.preventDefault();
    if (!userId.trim()) return;
    const override = Number(overrideDollars);
    const cents =
      Number.isFinite(override) && override > 0 ? Math.round(override * 100) : null;
    add.mutate(
      { user_id: userId.trim(), rate_override_cents: cents },
      {
        onSuccess: () => {
          setUserId("");
          setOverrideDollars("");
        },
      },
    );
  }

  return (
    <div
      role="region"
      aria-labelledby="members-heading"
      className="rounded-lg border bg-muted/30 p-4"
    >
      <h3 id="members-heading" className="text-lg font-semibold">
        Project members
      </h3>
      <form onSubmit={handleAdd} className="mt-3 flex flex-wrap items-end gap-3" aria-label="Add project member">
        <div className="space-y-1">
          <label htmlFor="member-user-id" className="block text-xs font-medium">
            User ID
          </label>
          <input
            id="member-user-id"
            value={userId}
            onChange={(event) => {
              setUserId(event.target.value);
            }}
            className="w-72 rounded-md border px-3 py-2 text-sm"
            placeholder="uuid…"
            required
          />
        </div>
        <div className="space-y-1">
          <label htmlFor="member-rate" className="block text-xs font-medium">
            Rate override ($/hr)
          </label>
          <input
            id="member-rate"
            type="number"
            min={0}
            value={overrideDollars}
            onChange={(event) => {
              setOverrideDollars(event.target.value);
            }}
            className="w-24 rounded-md border px-3 py-2 text-sm"
          />
        </div>
        <button
          type="submit"
          disabled={add.isPending}
          className="rounded-md bg-foreground px-3 py-2 text-sm font-medium text-background disabled:opacity-50"
        >
          {add.isPending ? "Adding…" : "Add member"}
        </button>
      </form>
      <ul className="mt-4 space-y-1 text-sm">
        {members.map((m) => (
          <li key={`${m.project_id}-${m.user_id}`}>
            {m.user_id}{" "}
            {m.rate_override_cents
              ? `• $${(m.rate_override_cents / 100).toFixed(2)}/hr override`
              : "• default rate"}
          </li>
        ))}
        {members.length === 0 && (
          <li className="text-muted-foreground">No members yet.</li>
        )}
      </ul>
    </div>
  );
}
