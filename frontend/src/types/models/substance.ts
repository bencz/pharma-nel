export interface PharmClassInfo {
  key: string;
  name: string;
  class_type: string | null;
}

export interface ManufacturerInfo {
  key: string;
  name: string;
}

export interface RouteInfo {
  key: string;
  name: string;
}

export interface DosageFormInfo {
  key: string;
  name: string;
}

export interface ProductInfo {
  key: string;
  product_number: string | null;
  package_ndc: string | null;
  brand_name: string | null;
  dosage_form: string | null;
  route: string | null;
  marketing_status: string | null;
  description: string | null;
}

export interface FDAApplicationInfo {
  key: string;
  application_number: string;
  submission_type: string | null;
  submission_number: string | null;
  submission_status: string | null;
  submission_status_date: string | null;
  review_priority: string | null;
}

export interface DrugLabelInfo {
  key: string;
  spl_id: string | null;
  set_id: string | null;
  version: string | null;
  effective_time: string | null;
  description: string | null;
  clinical_pharmacology: string | null;
  mechanism_of_action: string | null;
  indications_and_usage: string | null;
  dosage_and_administration: string | null;
  contraindications: string | null;
  warnings_and_cautions: string | null;
  boxed_warning: string | null;
  adverse_reactions: string | null;
  drug_interactions: string | null;
}

export interface InteractionInfo {
  key: string;
  severity: string | null;
  description: string | null;
  source_drug_rxcui: string | null;
  source_drug_name: string | null;
  target_drug_rxcui: string | null;
  target_drug_name: string | null;
}

export interface ReactionInfo {
  key: string;
  name: string;
  meddra_version: string | null;
}

export interface DrugInfo {
  key: string;
  application_number: string | null;
  brand_names: string[];
  generic_names: string[];
  ndc_codes: string[];
  rxcui: string[];
  spl_id: string[];
  sponsor_name: string | null;
  drug_type: string | null;
  source: string;
  is_enriched: boolean;
}

export interface SubstanceProfileData {
  key: string;
  name: string;
  unii: string | null;
  rxcui: string | null;
  cas_number: string | null;
  formula: string | null;
  molecular_weight: number | null;
  smiles: string | null;
  inchi: string | null;
  inchi_key: string | null;
  pubchem_id: string | null;
  substance_class: string | null;
  stereochemistry: string | null;
  is_enriched: boolean;
  enriched_at: string | null;
  drugs: DrugInfo[];
  pharm_classes: PharmClassInfo[];
  manufacturers: ManufacturerInfo[];
  routes: RouteInfo[];
  dosage_forms: DosageFormInfo[];
  products: ProductInfo[];
  applications: FDAApplicationInfo[];
  labels: DrugLabelInfo[];
  interactions: InteractionInfo[];
  reactions: ReactionInfo[];
}
