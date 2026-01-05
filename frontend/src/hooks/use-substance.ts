"use client";

import { useQuery } from "@tanstack/react-query";
import { entityApi } from "@/lib/api";

export const substanceKeys = {
  all: ["substances"] as const,
  detail: (id: string) => [...substanceKeys.all, "detail", id] as const,
};

export function useSubstance(substanceId: string | null) {
  return useQuery({
    queryKey: substanceKeys.detail(substanceId ?? ""),
    queryFn: () => entityApi.getSubstanceProfile(substanceId!),
    enabled: !!substanceId,
    staleTime: 1000 * 60 * 10,
    gcTime: 1000 * 60 * 30,
  });
}
