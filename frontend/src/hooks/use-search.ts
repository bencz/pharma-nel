"use client";

import { useQuery } from "@tanstack/react-query";
import { entityApi } from "@/lib/api";

export const searchKeys = {
  all: ["search"] as const,
  query: (q: string, limit: number) => [...searchKeys.all, q, limit] as const,
};

export function useSearch(query: string, limit = 20) {
  return useQuery({
    queryKey: searchKeys.query(query, limit),
    queryFn: () => entityApi.search(query, limit),
    enabled: query.length >= 2,
    staleTime: 1000 * 60 * 5,
  });
}
