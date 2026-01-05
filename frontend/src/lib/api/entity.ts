import type { EntitySearchResponse, SubstanceProfileResponse } from "@/types";
import { API_BASE_URL, handleResponse } from "./config";

export const entityApi = {
  async search(query: string, limit = 20): Promise<EntitySearchResponse> {
    const params = new URLSearchParams({ q: query, limit: String(limit) });
    const response = await fetch(`${API_BASE_URL}/entity?${params.toString()}`);
    return handleResponse<EntitySearchResponse>(response);
  },

  async getSubstanceProfile(substanceId: string): Promise<SubstanceProfileResponse> {
    const response = await fetch(`${API_BASE_URL}/entity/${encodeURIComponent(substanceId)}`);
    return handleResponse<SubstanceProfileResponse>(response);
  },
};
