export const API_BASE_URL = process.env.NEXT_PUBLIC_PHARMA_API_URL ?? "http://localhost:8000";

export class ApiError extends Error {
  constructor(
    message: string,
    public readonly code: string,
    public readonly statusCode: number,
    public readonly details?: Record<string, unknown>
  ) {
    super(message);
    this.name = "ApiError";
  }
}

export async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new ApiError(
      errorData.error?.message ?? "Request failed",
      errorData.error?.code ?? "UNKNOWN_ERROR",
      response.status,
      errorData.error?.details
    );
  }
  return response.json() as Promise<T>;
}
