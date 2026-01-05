export interface EntityNELResponse {
  name: string;
  type: string;
  linked_to: string | null;
  relationship: string | null;
  substance_id: string | null;
  url: string | null;
}

export interface EntitySearchResult {
  key: string;
  name: string;
  type: string;
  score: number | null;
}
