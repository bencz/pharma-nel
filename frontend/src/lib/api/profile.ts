import type { ProfilesListResponse, ProfileDetailResponse } from "@/types";
import { API_BASE_URL, handleResponse } from "./config";

export const profileApi = {
  async getProfiles(limit = 100): Promise<ProfilesListResponse> {
    const params = new URLSearchParams({ limit: String(limit) });
    const response = await fetch(`${API_BASE_URL}/profiles?${params.toString()}`);
    return handleResponse<ProfilesListResponse>(response);
  },

  async getById(profileId: string): Promise<ProfileDetailResponse> {
    const response = await fetch(`${API_BASE_URL}/profile/${encodeURIComponent(profileId)}`);
    return handleResponse<ProfileDetailResponse>(response);
  },
};
