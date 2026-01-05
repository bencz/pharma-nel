export interface ProfileLocationResponse {
  city: string | null;
  state: string | null;
  country: string | null;
}

export interface ProfileResponse {
  id: string;
  full_name: string | null;
  credentials: string[];
  email?: string | null;
  phone?: string | null;
  linkedin?: string | null;
  location?: ProfileLocationResponse | null;
}

export interface ProfileSummary {
  key: string;
  full_name: string | null;
  credentials: string[];
  email: string | null;
  extraction_count: number;
  substance_count: number;
}

export interface ProfilesListData {
  profiles: ProfileSummary[];
  count: number;
}

export interface ProfileExtractionSummary {
  key: string;
  filename: string;
  status: string;
  doc_type: string | null;
  therapeutic_areas: string[];
  total_entities: number;
  avg_confidence: number | null;
}

export interface ProfileSubstanceSummary {
  key: string;
  name: string;
  unii: string | null;
  is_enriched: boolean;
  drugs: Array<{ key: string; brand_names: string[] }>;
  routes: Array<{ key: string; name: string }>;
  dosage_forms: Array<{ key: string; name: string }>;
  pharm_classes: Array<{ key: string; name: string; class_type: string | null }>;
  manufacturers: Array<{ key: string; name: string }>;
}

export interface ProfileStats {
  total_extractions: number;
  total_substances: number;
}

export interface ProfileDetailData {
  profile: ProfileResponse;
  extractions: ProfileExtractionSummary[];
  substances: ProfileSubstanceSummary[];
  stats: ProfileStats;
}
