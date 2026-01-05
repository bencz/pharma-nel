"use client";

import { useQuery } from "@tanstack/react-query";
import { profileApi } from "@/lib/api";

export const profileKeys = {
  all: ["profiles"] as const,
  list: (limit: number) => [...profileKeys.all, "list", limit] as const,
  detail: (id: string) => [...profileKeys.all, "detail", id] as const,
};

export function useProfiles(limit = 100) {
  return useQuery({
    queryKey: profileKeys.list(limit),
    queryFn: () => profileApi.getProfiles(limit),
    staleTime: 30 * 1000,
  });
}

export function useProfileById(profileId: string | null) {
  return useQuery({
    queryKey: profileKeys.detail(profileId ?? ""),
    queryFn: () => profileApi.getById(profileId!),
    enabled: !!profileId,
  });
}
