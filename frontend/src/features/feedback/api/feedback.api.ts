/**
 * DTOs here mirror the backend's wire format (snake_case) on purpose, kept
 * separate from the camelCase domain types in ../types.ts - see
 * features/projects/api/projects.api.ts for the same pattern. `issues` and
 * `theory` need no field renaming (their keys are already plain words), so
 * they're reused as-is rather than remapped.
 */

import { httpClient } from "@/services/http";

import type { Feedback, FeedbackIssue, SkillLevel } from "../types";

interface FeedbackDto {
  id: string;
  composition_id: string;
  version_id: string;
  skill_level: SkillLevel;
  summary: string;
  strengths: string[];
  issues: FeedbackIssue[];
  suggestions: string[];
  model: string;
  created_at: string;
  updated_at: string;
}

function mapFeedback(dto: FeedbackDto): Feedback {
  return {
    id: dto.id,
    compositionId: dto.composition_id,
    versionId: dto.version_id,
    skillLevel: dto.skill_level,
    summary: dto.summary,
    strengths: dto.strengths,
    issues: dto.issues,
    suggestions: dto.suggestions,
    model: dto.model,
    createdAt: dto.created_at,
    updatedAt: dto.updated_at,
  };
}

export const feedbackApi = {
  /** Generates (or regenerates) AI feedback for the composition's newest
   *  analyzed version - this is the call that costs an AI request. */
  async generate(compositionId: string, skillLevel: SkillLevel): Promise<Feedback> {
    const { data } = await httpClient.post<FeedbackDto>(
      `/projects/${compositionId}/feedback`,
      null,
      { params: { skill_level: skillLevel } },
    );
    return mapFeedback(data);
  },

  /** Returns previously generated feedback, or throws (404) if none exists
   *  yet for this skill level - callers should treat that as "not generated
   *  yet", not as an error to surface. */
  async get(compositionId: string, skillLevel: SkillLevel): Promise<Feedback> {
    const { data } = await httpClient.get<FeedbackDto>(`/projects/${compositionId}/feedback`, {
      params: { skill_level: skillLevel },
    });
    return mapFeedback(data);
  },
};
