import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api } from "@/lib/api";
import { queryKeys } from "@/lib/queryKeys";
import type { Client } from "@/lib/types";

type ClientList = { clients: Client[] };

export function useClients() {
  return useQuery<Client[]>({
    queryKey: queryKeys.clients(),
    queryFn: async () => (await api.get<ClientList>("/clients")).clients,
  });
}

export type CreateClientInput = {
  name: string;
  email?: string | null;
  currency?: string;
};

export function useCreateClient() {
  const qc = useQueryClient();
  return useMutation<Client, Error, CreateClientInput>({
    mutationFn: (input) => api.post<Client>("/clients", input),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: queryKeys.clients() });
    },
  });
}
