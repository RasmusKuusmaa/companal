export type SkillLevel = "beginner" | "intermediate" | "advanced";

export const SKILL_LEVELS: SkillLevel[] = ["beginner", "intermediate", "advanced"];

export interface TheoryLesson {
  concept: string;
  lesson: string;
}

/** One weakness in the composition: what's wrong, why, how to fix it, and
 *  the theory concept it teaches - the AI never rewrites the music itself. */
export interface FeedbackIssue {
  problem: string;
  explanation: string;
  suggestion: string;
  theory: TheoryLesson;
}

export interface Feedback {
  id: string;
  compositionId: string;
  versionId: string;
  skillLevel: SkillLevel;
  summary: string;
  strengths: string[];
  issues: FeedbackIssue[];
  suggestions: string[];
  model: string;
  createdAt: string;
  updatedAt: string;
}
