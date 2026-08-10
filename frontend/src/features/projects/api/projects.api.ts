/**
 * DTOs here mirror the backend's wire format (snake_case, per its Pydantic
 * schemas) on purpose, kept separate from the camelCase domain types in
 * ../types.ts — the mapping functions are the one place that boundary is
 * allowed to leak. See features/auth/api/auth.api.ts for the same pattern.
 */

import { httpClient } from "@/services/http";

import type {
  Composition,
  CompositionAnalysis,
  CreateCompositionPayload,
  EngineAnalysis,
  RenameCompositionPayload,
  UnavailableEngine,
  Version,
} from "../types";

interface CompositionDto {
  id: string;
  title: string;
  version_count: number;
  created_at: string;
  updated_at: string;
}

interface VersionDto {
  id: string;
  composition_id: string;
  version_number: number;
  original_filename: string;
  file_size: number;
  created_at: string;
}

function mapComposition(dto: CompositionDto): Composition {
  return {
    id: dto.id,
    title: dto.title,
    versionCount: dto.version_count,
    createdAt: dto.created_at,
    updatedAt: dto.updated_at,
  };
}

interface EngineAnalysisDto {
  score: number;
  strengths: string[];
  issues: string[];
}

interface CompositionAnalysisDto {
  composition_id: string;
  version_id: string;
  version_number: number;
  overall_score: number;
  melody_analysis: EngineAnalysisDto | null;
  harmony_analysis: EngineAnalysisDto | null;
  rhythm_analysis: EngineAnalysisDto | null;
  unavailable: UnavailableEngine[];
  analyzed_at: string;
}

function mapEngineAnalysis(dto: EngineAnalysisDto | null): EngineAnalysis | null {
  if (!dto) return null;
  return { score: dto.score, strengths: dto.strengths, issues: dto.issues };
}

function mapCompositionAnalysis(dto: CompositionAnalysisDto): CompositionAnalysis {
  return {
    compositionId: dto.composition_id,
    versionId: dto.version_id,
    versionNumber: dto.version_number,
    overallScore: dto.overall_score,
    melody: mapEngineAnalysis(dto.melody_analysis),
    harmony: mapEngineAnalysis(dto.harmony_analysis),
    rhythm: mapEngineAnalysis(dto.rhythm_analysis),
    unavailable: dto.unavailable,
    analyzedAt: dto.analyzed_at,
  };
}

function mapVersion(dto: VersionDto): Version {
  return {
    id: dto.id,
    compositionId: dto.composition_id,
    versionNumber: dto.version_number,
    originalFilename: dto.original_filename,
    fileSize: dto.file_size,
    createdAt: dto.created_at,
  };
}

export const projectsApi = {
  async list(): Promise<Composition[]> {
    const { data } = await httpClient.get<CompositionDto[]>("/projects");
    return data.map(mapComposition);
  },

  async create(payload: CreateCompositionPayload): Promise<Composition> {
    const { data } = await httpClient.post<CompositionDto>("/projects", payload);
    return mapComposition(data);
  },

  async get(id: string): Promise<Composition> {
    const { data } = await httpClient.get<CompositionDto>(`/projects/${id}`);
    return mapComposition(data);
  },

  async rename(id: string, payload: RenameCompositionPayload): Promise<Composition> {
    const { data } = await httpClient.patch<CompositionDto>(`/projects/${id}`, payload);
    return mapComposition(data);
  },

  async remove(id: string): Promise<void> {
    await httpClient.delete(`/projects/${id}`);
  },

  async listVersions(compositionId: string): Promise<Version[]> {
    const { data } = await httpClient.get<VersionDto[]>(`/projects/${compositionId}/versions`);
    return data.map(mapVersion);
  },

  async uploadVersion(compositionId: string, file: File): Promise<Version> {
    const formData = new FormData();
    formData.append("file", file);
    const { data } = await httpClient.post<VersionDto>(
      `/projects/${compositionId}/versions`,
      formData,
    );
    return mapVersion(data);
  },

  async downloadVersion(compositionId: string, versionId: string): Promise<Blob> {
    const { data } = await httpClient.get<Blob>(
      `/projects/${compositionId}/versions/${versionId}/file`,
      { responseType: "blob" },
    );
    return data;
  },

  /** Runs (or re-runs) the melody/harmony/rhythm engines over the newest
   *  version and returns the combined result. Deterministic and free of AI
   *  cost, so it's safe to call whenever the dashboard needs fresh scores. */
  async analyze(compositionId: string): Promise<CompositionAnalysis> {
    const { data } = await httpClient.post<CompositionAnalysisDto>(
      `/projects/${compositionId}/analyze`,
    );
    return mapCompositionAnalysis(data);
  },
};
