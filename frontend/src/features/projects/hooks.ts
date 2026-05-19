import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api } from "@/lib/api";
import { queryKeys } from "@/lib/queryKeys";
import type { Project, ProjectMember } from "@/lib/types";

type ProjectList = { projects: Project[] };
type MemberList = { members: ProjectMember[] };

export function useProjects(clientId?: string) {
  return useQuery<Project[]>({
    queryKey: queryKeys.projects(),
    queryFn: async () =>
      (await api.get<ProjectList>("/projects", clientId ? { client_id: clientId } : undefined))
        .projects,
  });
}

export type CreateProjectInput = {
  client_id: string;
  name: string;
  default_rate_cents?: number | null;
  rounding_minutes?: number;
  billable?: boolean;
};

export function useCreateProject() {
  const qc = useQueryClient();
  return useMutation<Project, Error, CreateProjectInput>({
    mutationFn: (input) => api.post<Project>("/projects", input),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: queryKeys.projects() });
    },
  });
}

export function useProjectMembers(projectId: string | undefined) {
  return useQuery<ProjectMember[]>({
    queryKey: ["project-members", projectId],
    queryFn: async () =>
      (await api.get<MemberList>(`/projects/${projectId ?? ""}/members`)).members,
    enabled: !!projectId,
  });
}

export function useAddProjectMember(projectId: string) {
  const qc = useQueryClient();
  return useMutation<
    ProjectMember,
    Error,
    { user_id: string; rate_override_cents: number | null }
  >({
    mutationFn: (input) =>
      api.post<ProjectMember>(`/projects/${projectId}/members`, input),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: ["project-members", projectId] });
    },
  });
}
