import type { ProfileResponse } from "./profile";
import type { EntityNELResponse } from "./entity";

export interface ExtractAndEnrichDataResponse {
  extraction_id: string;
  profile: ProfileResponse | null;
  entities: EntityNELResponse[];
}

export interface ExtractionSummary {
  key: string;
  file_hash: string;
  filename: string;
  status: string;
  created_at: string;
  doc_type: string | null;
  therapeutic_areas: string[];
  drug_density: string | null;
  total_entities: number;
  avg_confidence: number | null;
  profile: ProfileResponse | null;
}

export interface ExtractionsListData {
  extractions: ExtractionSummary[];
  count: number;
}
