import type { ExtractAndEnrichResponse, ExtractionsListResponse } from "@/types";
import { API_BASE_URL, handleResponse } from "./config";

export const extractionApi = {
  async extractFromPdf(file: File): Promise<ExtractAndEnrichResponse> {
    const formData = new FormData();
    formData.append("file", file);

    const response = await fetch(`${API_BASE_URL}/extract`, {
      method: "POST",
      body: formData,
    });

    return handleResponse<ExtractAndEnrichResponse>(response);
  },

  async getExtractions(limit = 100): Promise<ExtractionsListResponse> {
    const params = new URLSearchParams({ limit: String(limit) });
    const response = await fetch(`${API_BASE_URL}/extractions?${params.toString()}`);
    return handleResponse<ExtractionsListResponse>(response);
  },

  async getById(extractionId: string): Promise<ExtractAndEnrichResponse> {
    const response = await fetch(`${API_BASE_URL}/extract/${encodeURIComponent(extractionId)}`);
    return handleResponse<ExtractAndEnrichResponse>(response);
  },
};
