/**
 * Domain types for exams, in the app's camelCase convention. The
 * snake_case wire shapes live in api/exams.api.ts, the only place the two
 * are allowed to meet - same split as features/learning.
 *
 * `ExamQuestion` is a discriminated union on `kind`, narrower than
 * `LessonStep`'s: an exam is an assessment, not a lesson, so there is no
 * `reading` question to answer (see the backend's `ExamQuestionKind`).
 */

import type { Requirement } from "@/features/learning/types";
import type { NotationDocument } from "@/features/notation/types";

export type ExamQuestionKind = "quiz" | "composition";

interface ExamQuestionBase {
  id: string;
  slug: string;
  position: number;
}

export interface ExamQuizQuestion extends ExamQuestionBase {
  kind: "quiz";
  question: string;
  choices: string[];
}

export interface ExamCompositionQuestion extends ExamQuestionBase {
  kind: "composition";
  brief: string;
  requirements: Requirement[];
  starterNotation: NotationDocument | null;
  lockedStaffIndices: number[];
}

export type ExamQuestion = ExamQuizQuestion | ExamCompositionQuestion;

export interface ExamSummary {
  id: string;
  slug: string;
  title: string;
  description: string;
  /** Null for the comprehensive final, which isn't scoped to one stage. */
  courseSlug: string | null;
  questionCount: number;
}

export interface Exam extends ExamSummary {
  questions: ExamQuestion[];
}

export interface ExamAttemptStart {
  attemptId: string;
  attemptNumber: number;
  exam: Exam;
  startedAt: string;
}

export type ExamAnswerPayload =
  { kind: "quiz"; choiceIndex: number } | { kind: "composition"; document: NotationDocument };

export interface ExamAnswerResult {
  questionId: string;
  answered: boolean;
}

/** One question's graded result within a submitted attempt. `detail` is
 *  shaped like a quiz's correctness/explanation or a composition's full
 *  deterministic grade (and AI commentary, for premium) - see the
 *  backend's `ExamQuestionResultRead`. */
export interface ExamQuestionResult {
  questionId: string;
  kind: ExamQuestionKind;
  score: number;
  maxScore: number;
  detail: Record<string, unknown>;
}

export interface ExamAttemptResult {
  attemptId: string;
  attemptNumber: number;
  score: number;
  maxScore: number;
  submittedAt: string;
  questionResults: ExamQuestionResult[];
}

export interface ExamAttemptSummary {
  attemptId: string;
  attemptNumber: number;
  score: number | null;
  maxScore: number | null;
  startedAt: string;
  submittedAt: string | null;
}

export interface ExamAttemptHistory {
  examSlug: string;
  attempts: ExamAttemptSummary[];
}
