import type {
  BaseResponse,
  ExtractAndEnrichDataResponse,
  ExtractionsListData,
  EntitySearchResult,
  SubstanceProfileData,
  ProfilesListData,
  ProfileDetailData,
} from "../models";

export type ExtractAndEnrichResponse = BaseResponse<ExtractAndEnrichDataResponse>;

export type ExtractionsListResponse = BaseResponse<ExtractionsListData>;

export type EntitySearchResponse = BaseResponse<EntitySearchResult[]>;

export type SubstanceProfileResponse = BaseResponse<SubstanceProfileData>;

export type ProfilesListResponse = BaseResponse<ProfilesListData>;

export type ProfileDetailResponse = BaseResponse<ProfileDetailData>;
