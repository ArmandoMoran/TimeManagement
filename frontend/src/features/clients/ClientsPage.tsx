import { useState } from "react";

import { useClients, useCreateClient } from "./hooks";

export function ClientsPage(): React.ReactElement {
  const { data: clients = [], isLoading } = useClients();
  const create = useCreateClient();
  const [name, setName] = useState<string>("");
  const [email, setEmail] = useState<string>("");

  function handleCreate(event: React.SyntheticEvent<HTMLFormElement>): void {
    event.preventDefault();
    if (!name.trim()) return;
    create.mutate(
      { name: name.trim(), email: email.trim() || null },
      {
        onSuccess: () => {
          setName("");
          setEmail("");
        },
      },
    );
  }

  return (
    <section aria-labelledby="clients-heading" className="space-y-6">
      <h2 id="clients-heading" className="text-2xl font-semibold">
        Clients
      </h2>

      <form onSubmit={handleCreate} className="flex flex-wrap items-end gap-3" aria-label="New client">
        <div className="space-y-1">
          <label htmlFor="client-name" className="block text-xs font-medium">
            Name
          </label>
          <input
            id="client-name"
            value={name}
            onChange={(event) => {
              setName(event.target.value);
            }}
            className="rounded-md border px-3 py-2 text-sm"
            required
          />
        </div>
        <div className="space-y-1">
          <label htmlFor="client-email" className="block text-xs font-medium">
            Email
          </label>
          <input
            id="client-email"
            type="email"
            value={email}
            onChange={(event) => {
              setEmail(event.target.value);
            }}
            className="rounded-md border px-3 py-2 text-sm"
          />
        </div>
        <button
          type="submit"
          disabled={create.isPending}
          className="rounded-md bg-primary px-3 py-2 text-sm font-medium text-primary-foreground disabled:opacity-50"
        >
          {create.isPending ? "Creating…" : "Create client"}
        </button>
        {create.isError && (
          <p role="alert" className="text-sm text-red-600">
            {create.error.message}
          </p>
        )}
      </form>

      {isLoading ? (
        <p>Loading…</p>
      ) : clients.length === 0 ? (
        <p className="text-sm text-muted-foreground">No clients yet. Create one above.</p>
      ) : (
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b text-left">
              <th className="py-2 pr-4 font-medium">Name</th>
              <th className="py-2 pr-4 font-medium">Email</th>
              <th className="py-2 pr-4 font-medium">Currency</th>
            </tr>
          </thead>
          <tbody>
            {clients.map((c) => (
              <tr key={c.id} className="border-b last:border-0">
                <td className="py-2 pr-4">{c.name}</td>
                <td className="py-2 pr-4">{c.email ?? "—"}</td>
                <td className="py-2 pr-4">{c.currency}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </section>
  );
}
