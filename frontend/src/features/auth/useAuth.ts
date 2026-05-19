import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";

import { api } from "@/lib/api";
import type { ApiError } from "@/lib/api";
import { queryKeys } from "@/lib/queryKeys";
import { tokenStore } from "@/lib/tokenStore";
import type { TokensResponse, User } from "@/lib/types";

function hasToken(): boolean {
  return tokenStore.getAccessToken() !== null;
}

export function useCurrentUser(): {
  user: User | undefined;
  isLoading: boolean;
  isAuthenticated: boolean;
  error: ApiError | null;
} {
  const [authPresent, setAuthPresent] = useState<boolean>(hasToken());

  useEffect(() => {
    const unsubscribe = tokenStore.subscribe(() => {
      setAuthPresent(hasToken());
    });
    return unsubscribe;
  }, []);

  const query = useQuery<User, ApiError>({
    queryKey: queryKeys.me,
    queryFn: () => api.get<User>("/auth/me"),
    enabled: authPresent,
    retry: false,
    staleTime: 60_000,
  });

  return {
    user: query.data,
    isLoading: authPresent && query.isLoading,
    isAuthenticated: authPresent && !query.isError,
    error: query.error ?? null,
  };
}

export function useLogin(): {
  mutate: (credentials: { email: string; password: string }) => void;
  mutateAsync: (credentials: { email: string; password: string }) => Promise<TokensResponse>;
  isPending: boolean;
  error: ApiError | null;
} {
  const queryClient = useQueryClient();

  const mutation = useMutation<
    TokensResponse,
    ApiError,
    { email: string; password: string }
  >({
    mutationFn: (credentials) => api.post<TokensResponse>("/auth/login", credentials),
    onSuccess: (data) => {
      tokenStore.setTokens(data.access_token, data.refresh_token);
      queryClient.setQueryData(queryKeys.me, data.user);
    },
  });

  return {
    mutate: mutation.mutate,
    mutateAsync: mutation.mutateAsync,
    isPending: mutation.isPending,
    error: mutation.error,
  };
}

export function useLogout(): { logout: () => Promise<void> } {
  const queryClient = useQueryClient();
  return {
    logout: async () => {
      try {
        await api.post("/auth/logout");
      } catch {
        // Server may already have invalidated; clear locally regardless.
      }
      tokenStore.clear();
      queryClient.removeQueries({ queryKey: queryKeys.me });
    },
  };
}
