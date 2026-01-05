import { extractionApi, entityApi, profileApi, healthApi, ApiError } from "./api";

export const apiClient = {
  extractFromPdf: extractionApi.extractFromPdf,
  getSubstanceProfile: entityApi.getSubstanceProfile,
  searchEntities: entityApi.search,
  checkHealth: healthApi.check,
  getExtractions: extractionApi.getExtractions,
  getExtractionById: extractionApi.getById,
  getProfiles: profileApi.getProfiles,
  getProfileById: profileApi.getById,
};

export { ApiError };
