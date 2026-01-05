import { create } from "zustand";
import type { ExtractAndEnrichDataResponse, EntityNELResponse } from "@/types";

interface ExtractionState {
  extractionResult: ExtractAndEnrichDataResponse | null;
  selectedEntity: EntityNELResponse | null;
  selectedSubstanceId: string | null;
  selectedExtractionId: string | null;
  selectedProfileId: string | null;
  isDetailsPanelOpen: boolean;
  isProfilePanelOpen: boolean;
}

interface ExtractionActions {
  setExtractionResult: (result: ExtractAndEnrichDataResponse | null) => void;
  setSelectedEntity: (entity: EntityNELResponse | null) => void;
  setSelectedSubstanceId: (id: string | null) => void;
  setSelectedExtractionId: (id: string | null) => void;
  setSelectedProfileId: (id: string | null) => void;
  openDetailsPanel: () => void;
  closeDetailsPanel: () => void;
  openProfilePanel: () => void;
  closeProfilePanel: () => void;
  reset: () => void;
}

type ExtractionStore = ExtractionState & ExtractionActions;

export const useExtractionStore = create<ExtractionStore>((set) => ({
  extractionResult: null,
  selectedEntity: null,
  selectedSubstanceId: null,
  selectedExtractionId: null,
  selectedProfileId: null,
  isDetailsPanelOpen: false,
  isProfilePanelOpen: false,
  setExtractionResult: (result) => set({ extractionResult: result, selectedExtractionId: null }),
  setSelectedEntity: (entity) =>
    set({
      selectedEntity: entity,
      selectedSubstanceId: entity?.substance_id ?? null,
      isDetailsPanelOpen: !!entity?.substance_id,
    }),
  setSelectedSubstanceId: (id) =>
    set({ selectedSubstanceId: id, isDetailsPanelOpen: !!id }),
  setSelectedExtractionId: (id) =>
    set({ selectedExtractionId: id, extractionResult: null }),
  setSelectedProfileId: (id) =>
    set({ selectedProfileId: id, isProfilePanelOpen: !!id }),
  openDetailsPanel: () => set({ isDetailsPanelOpen: true }),
  closeDetailsPanel: () => set({ isDetailsPanelOpen: false }),
  openProfilePanel: () => set({ isProfilePanelOpen: true }),
  closeProfilePanel: () => set({ isProfilePanelOpen: false, selectedProfileId: null }),
  reset: () =>
    set({
      extractionResult: null,
      selectedEntity: null,
      selectedSubstanceId: null,
      selectedExtractionId: null,
      selectedProfileId: null,
      isDetailsPanelOpen: false,
      isProfilePanelOpen: false,
    }),
}));
