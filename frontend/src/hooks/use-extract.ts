"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { extractionApi, entityApi } from "@/lib/api";
import type { ExtractAndEnrichResponse } from "@/types";

export function useExtract() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (file: File) => extractionApi.extractFromPdf(file),
    onSuccess: (data: ExtractAndEnrichResponse) => {
      if (data.data?.entities) {
        data.data.entities.forEach((entity) => {
          if (entity.substance_id) {
            queryClient.prefetchQuery({
              queryKey: ["substance", entity.substance_id],
              queryFn: () => entityApi.getSubstanceProfile(entity.substance_id!),
              staleTime: 1000 * 60 * 5,
            });
          }
        });
      }
    },
  });
}
