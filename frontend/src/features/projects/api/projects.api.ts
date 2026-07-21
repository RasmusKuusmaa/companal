/**
 * DTOs here mirror the backend's wire format (snake_case, per its Pydantic
 * schemas) on purpose, kept separate from the camelCase domain types in
 * ../types.ts — the mapping functions are the one place that boundary is
 * allowed to leak. See features/auth/api/auth.api.ts for the same pattern.
 */

import { httpClient } from "@/services/http";

import type {
  Composition,
  CreateCompositionPayload,
  RenameCompositionPayload,
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
};
