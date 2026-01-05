import { API_BASE_URL, handleResponse } from "./config";

export const healthApi = {
  async check(): Promise<{ status: string }> {
    const response = await fetch(`${API_BASE_URL}/health/live`);
    return handleResponse<{ status: string }>(response);
  },
};
