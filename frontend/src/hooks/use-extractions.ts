"use client";

import { useQuery } from "@tanstack/react-query";
import { extractionApi } from "@/lib/api";

export const extractionKeys = {
  all: ["extractions"] as const,
  list: (limit: number) => [...extractionKeys.all, "list", limit] as const,
  detail: (id: string) => [...extractionKeys.all, "detail", id] as const,
};

export function useExtractions(limit = 100) {
  return useQuery({
    queryKey: extractionKeys.list(limit),
    queryFn: () => extractionApi.getExtractions(limit),
    staleTime: 30 * 1000,
  });
}

export function useExtractionById(extractionId: string | null) {
  return useQuery({
    queryKey: extractionKeys.detail(extractionId ?? ""),
    queryFn: () => extractionApi.getById(extractionId!),
    enabled: !!extractionId,
  });
}
