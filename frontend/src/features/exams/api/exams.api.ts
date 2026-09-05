/**
 * DTOs mirror the backend's snake_case wire format; the mapping functions
 * below are the only place that convention is allowed to leak into the
 * app - same pattern as features/learning/api/learning.api.ts.
 */

import { httpClient } from "@/services/http";
import type { SkillLevel } from "@/features/feedback/types";
import type { Requirement } from "@/features/learning/types";
import {
  notationDocumentFromDto,
  notationDocumentToDto,
  type NotationDocumentDto,
} from "@/features/notation/api";

import type {
  Exam,
  ExamAnswerPayload,
  ExamAnswerResult,
  ExamAttemptHistory,
  ExamAttemptResult,
  ExamAttemptStart,
  ExamQuestion,
  ExamSummary,
} from "../types";

type RequirementDto = Record<string, unknown>;

function mapRequirement(dto: RequirementDto): Requirement {
  return dto as unknown as Requirement;
}

type ExamQuestionDto =
  | {
      kind: "quiz";
      id: string;
      slug: string;
      position: number;
      question: string;
      choices: string[];
    }
  | {
      kind: "composition";
      id: string;
      slug: string;
      position: number;
      brief: string;
      requirements: RequirementDto[];
      starter_notation: NotationDocumentDto | null;
      locked_staff_indices: number[];
    };

interface ExamSummaryDto {
  id: string;
  slug: string;
  title: string;
  description: string;
  course_slug: string | null;
  question_count: number;
}

interface ExamDto extends ExamSummaryDto {
  questions: ExamQuestionDto[];
}

interface ExamAttemptStartDto {
  attempt_id: string;
  attempt_number: number;
  exam: ExamDto;
  started_at: string;
}

interface ExamAnswerResultDto {
  question_id: string;
  answered: boolean;
}

interface ExamQuestionResultDto {
  question_id: string;
  kind: "quiz" | "composition";
  score: number;
  max_score: number;
  detail: Record<string, unknown>;
}

interface ExamAttemptResultDto {
  attempt_id: string;
  attempt_number: number;
  score: number;
  max_score: number;
  submitted_at: string;
  question_results: ExamQuestionResultDto[];
}

interface ExamAttemptSummaryDto {
  attempt_id: string;
  attempt_number: number;
  score: number | null;
  max_score: number | null;
  started_at: string;
  submitted_at: string | null;
}

interface ExamAttemptHistoryDto {
  exam_slug: string;
  attempts: ExamAttemptSummaryDto[];
}

function mapQuestion(dto: ExamQuestionDto): ExamQuestion {
  const base = { id: dto.id, slug: dto.slug, position: dto.position };
  switch (dto.kind) {
    case "quiz":
      return { ...base, kind: "quiz", question: dto.question, choices: dto.choices };
    case "composition":
      return {
        ...base,
        kind: "composition",
        brief: dto.brief,
        requirements: dto.requirements.map(mapRequirement),
        starterNotation: dto.starter_notation
          ? notationDocumentFromDto(dto.starter_notation)
          : null,
        lockedStaffIndices: dto.locked_staff_indices,
      };
  }
}

function mapExamSummary(dto: ExamSummaryDto): ExamSummary {
  return {
    id: dto.id,
    slug: dto.slug,
    title: dto.title,
    description: dto.description,
    courseSlug: dto.course_slug,
    questionCount: dto.question_count,
  };
}

function mapExam(dto: ExamDto): Exam {
  return {
    ...mapExamSummary(dto),
    questions: dto.questions.map(mapQuestion),
  };
}

function mapAttemptStart(dto: ExamAttemptStartDto): ExamAttemptStart {
  return {
    attemptId: dto.attempt_id,
    attemptNumber: dto.attempt_number,
    exam: mapExam(dto.exam),
    startedAt: dto.started_at,
  };
}

function mapQuestionResult(
  dto: ExamQuestionResultDto,
): ExamAttemptResult["questionResults"][number] {
  return {
    questionId: dto.question_id,
    kind: dto.kind,
    score: dto.score,
    maxScore: dto.max_score,
    detail: dto.detail,
  };
}

function mapAttemptResult(dto: ExamAttemptResultDto): ExamAttemptResult {
  return {
    attemptId: dto.attempt_id,
    attemptNumber: dto.attempt_number,
    score: dto.score,
    maxScore: dto.max_score,
    submittedAt: dto.submitted_at,
    questionResults: dto.question_results.map(mapQuestionResult),
  };
}

function mapAttemptHistory(dto: ExamAttemptHistoryDto): ExamAttemptHistory {
  return {
    examSlug: dto.exam_slug,
    attempts: dto.attempts.map((attempt) => ({
      attemptId: attempt.attempt_id,
      attemptNumber: attempt.attempt_number,
      score: attempt.score,
      maxScore: attempt.max_score,
      startedAt: attempt.started_at,
      submittedAt: attempt.submitted_at,
    })),
  };
}

function mapAnswerPayload(answer: ExamAnswerPayload): Record<string, unknown> {
  if (answer.kind === "quiz") {
    return { kind: "quiz", choice_index: answer.choiceIndex };
  }
  return { kind: "composition", document: notationDocumentToDto(answer.document) };
}

export const examsApi = {
  /** Every exam, in position order - one per stage, plus the final. */
  async listExams(): Promise<ExamSummary[]> {
    const { data } = await httpClient.get<ExamSummaryDto[]>("/exams");
    return data.map(mapExamSummary);
  },

  /** Starts a new attempt - always a fresh one, never a resume. */
  async startAttempt(examSlug: string): Promise<ExamAttemptStart> {
    const { data } = await httpClient.post<ExamAttemptStartDto>(`/exams/${examSlug}/attempts`);
    return mapAttemptStart(data);
  },

  /**
   * Holds one answer. Nothing is graded until the attempt is submitted,
   * and answering the same question again replaces what was held.
   */
  async answerQuestion(
    attemptId: string,
    questionId: string,
    answer: ExamAnswerPayload,
  ): Promise<ExamAnswerResult> {
    const { data } = await httpClient.post<ExamAnswerResultDto>(
      `/exams/attempts/${attemptId}/questions/${questionId}/answer`,
      { answer: mapAnswerPayload(answer) },
    );
    return { questionId: data.question_id, answered: data.answered };
  },

  /**
   * Grades every held answer and marks the attempt submitted.
   * `withAiFeedback` is a hard tier gate for exams, not a quota - asking
   * without premium comes back as a 402 the caller has to handle, not a
   * quietly empty `ai_feedback`.
   */
  async submitAttempt(
    attemptId: string,
    withAiFeedback: boolean,
    skillLevel: SkillLevel,
  ): Promise<ExamAttemptResult> {
    const { data } = await httpClient.post<ExamAttemptResultDto>(
      `/exams/attempts/${attemptId}/submit`,
      { with_ai_feedback: withAiFeedback, skill_level: skillLevel },
    );
    return mapAttemptResult(data);
  },

  async getAttemptHistory(examSlug: string): Promise<ExamAttemptHistory> {
    const { data } = await httpClient.get<ExamAttemptHistoryDto>(`/exams/${examSlug}/history`);
    return mapAttemptHistory(data);
  },
};
