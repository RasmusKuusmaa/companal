/**
 * DTOs mirror the backend's snake_case wire format; the mapping functions
 * below are the only place that convention is allowed to leak into the app.
 * Same pattern as features/projects/api/projects.api.ts.
 *
 * The step mapper switches on `kind` rather than spreading the DTO, so a
 * field the backend adds can't silently arrive in the UI's domain type
 * unmapped - and a new step kind is a compile error here first.
 */

import { httpClient } from "@/services/http";
import {
  notationDocumentFromDto,
  notationDocumentToDto,
  type NotationDocumentDto,
} from "@/features/notation/api";
import type { NotationDocument } from "@/features/notation/types";

import type {
  CadenceKind,
  CompositionAiFeedback,
  CompositionSubmissionResult,
  Lesson,
  LessonCompletion,
  LessonStep,
  LessonSummary,
  ProgressSummary,
  QuizAnswerResult,
  Requirement,
  RequirementResult,
  Roadmap,
  SkillLevel,
  StepSeen,
} from "../types";

type RequirementDto =
  | { type: "key"; key: string }
  | { type: "time_signature"; value: string }
  | { type: "measure_count"; count: number }
  | { type: "cadence"; cadence: CadenceKind }
  | { type: "range"; max_semitones: number | null; lowest: string | null; highest: string | null }
  | { type: "max_leap"; semitones: number }
  | { type: "leap_recovery"; max_unresolved: number }
  | { type: "diatonic_only" }
  | { type: "required_scale_degrees"; degrees: number[] }
  | { type: "forbidden_pitches"; pitches: string[] };

function mapRequirement(dto: RequirementDto): Requirement {
  switch (dto.type) {
    case "range":
      return {
        type: "range",
        maxSemitones: dto.max_semitones,
        lowest: dto.lowest,
        highest: dto.highest,
      };
    case "leap_recovery":
      return { type: "leap_recovery", maxUnresolved: dto.max_unresolved };
    default:
      return dto;
  }
}

interface LessonSummaryDto {
  id: string;
  slug: string;
  title: string;
  summary: string;
  position: number;
  estimated_minutes: number;
  step_count: number;
  status: LessonSummary["status"];
  completed_at: string | null;
}

interface CourseDto {
  id: string;
  slug: string;
  title: string;
  description: string;
  level: "beginner" | "intermediate" | "advanced";
  position: number;
  lesson_count: number;
  completed_lesson_count: number;
  lessons: LessonSummaryDto[];
}

interface RoadmapDto {
  courses: CourseDto[];
  lesson_count: number;
  completed_lesson_count: number;
  in_progress_lesson_count: number;
}

type StepDto =
  | { kind: "reading"; id: string; slug: string; position: number; markdown: string }
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
    };

interface LessonDto {
  id: string;
  slug: string;
  title: string;
  summary: string;
  position: number;
  estimated_minutes: number;
  course: { id: string; slug: string; title: string };
  status: Lesson["status"];
  current_step_id: string | null;
  completed_at: string | null;
  steps: StepDto[];
  previous_lesson_slug: string | null;
  next_lesson_slug: string | null;
}

interface QuizAnswerResultDto {
  attempt_id: string;
  is_correct: boolean;
  correct_index: number;
  explanation: string;
}

interface StepSeenDto {
  lesson_id: string;
  current_step_id: string | null;
  status: Lesson["status"];
}

interface RequirementResultDto {
  requirement: RequirementDto;
  passed: boolean;
  message: string;
  measure: number | null;
}

function mapRequirementResult(dto: RequirementResultDto): RequirementResult {
  return {
    requirement: mapRequirement(dto.requirement),
    passed: dto.passed,
    message: dto.message,
    measure: dto.measure,
  };
}

interface CompositionAiFeedbackDto {
  summary: string;
  strengths: string[];
  issues: {
    problem: string;
    explanation: string;
    suggestion: string;
    theory: { concept: string; lesson: string };
  }[];
  suggestions: string[];
}

function mapCompositionAiFeedback(dto: CompositionAiFeedbackDto): CompositionAiFeedback {
  return {
    summary: dto.summary,
    strengths: dto.strengths,
    issues: dto.issues,
    suggestions: dto.suggestions,
  };
}

interface CompositionSubmissionDto {
  attempt_id: string;
  created_at: string;
  requirement_results: RequirementResultDto[];
  passed: boolean;
  overall_score: number | null;
  ai_feedback: CompositionAiFeedbackDto | null;
}

function mapCompositionSubmission(dto: CompositionSubmissionDto): CompositionSubmissionResult {
  return {
    attemptId: dto.attempt_id,
    createdAt: dto.created_at,
    requirementResults: dto.requirement_results.map(mapRequirementResult),
    passed: dto.passed,
    overallScore: dto.overall_score,
    aiFeedback: dto.ai_feedback ? mapCompositionAiFeedback(dto.ai_feedback) : null,
  };
}

interface LessonCompletionDto {
  lesson_id: string;
  status: Lesson["status"];
  completed_at: string;
  next_lesson_slug: string | null;
}

interface ProgressSummaryDto {
  lesson_count: number;
  completed_lesson_count: number;
  in_progress_lesson_count: number;
  by_course: {
    course_id: string;
    course_slug: string;
    course_title: string;
    lesson_count: number;
    completed_lesson_count: number;
    in_progress_lesson_count: number;
  }[];
  continue_lesson_slug: string | null;
  continue_lesson_title: string | null;
}

function mapLessonSummary(dto: LessonSummaryDto): LessonSummary {
  return {
    id: dto.id,
    slug: dto.slug,
    title: dto.title,
    summary: dto.summary,
    position: dto.position,
    estimatedMinutes: dto.estimated_minutes,
    stepCount: dto.step_count,
    status: dto.status,
    completedAt: dto.completed_at,
  };
}

function mapRoadmap(dto: RoadmapDto): Roadmap {
  return {
    courses: dto.courses.map((course) => ({
      id: course.id,
      slug: course.slug,
      title: course.title,
      description: course.description,
      level: course.level,
      position: course.position,
      lessonCount: course.lesson_count,
      completedLessonCount: course.completed_lesson_count,
      lessons: course.lessons.map(mapLessonSummary),
    })),
    lessonCount: dto.lesson_count,
    completedLessonCount: dto.completed_lesson_count,
    inProgressLessonCount: dto.in_progress_lesson_count,
  };
}

function mapStep(dto: StepDto): LessonStep {
  const base = { id: dto.id, slug: dto.slug, position: dto.position };
  switch (dto.kind) {
    case "reading":
      return { ...base, kind: "reading", markdown: dto.markdown };
    case "quiz":
      return { ...base, kind: "quiz", question: dto.question, choices: dto.choices };
    case "composition":
      return {
        ...base,
        kind: "composition",
        brief: dto.brief,
        requirements: dto.requirements.map(mapRequirement),
        starterNotation: dto.starter_notation ? notationDocumentFromDto(dto.starter_notation) : null,
      };
  }
}

function mapLesson(dto: LessonDto): Lesson {
  return {
    id: dto.id,
    slug: dto.slug,
    title: dto.title,
    summary: dto.summary,
    position: dto.position,
    estimatedMinutes: dto.estimated_minutes,
    course: dto.course,
    status: dto.status,
    currentStepId: dto.current_step_id,
    completedAt: dto.completed_at,
    steps: dto.steps.map(mapStep),
    previousLessonSlug: dto.previous_lesson_slug,
    nextLessonSlug: dto.next_lesson_slug,
  };
}

function mapProgressSummary(dto: ProgressSummaryDto): ProgressSummary {
  return {
    lessonCount: dto.lesson_count,
    completedLessonCount: dto.completed_lesson_count,
    inProgressLessonCount: dto.in_progress_lesson_count,
    byCourse: dto.by_course.map((course) => ({
      courseId: course.course_id,
      courseSlug: course.course_slug,
      courseTitle: course.course_title,
      lessonCount: course.lesson_count,
      completedLessonCount: course.completed_lesson_count,
      inProgressLessonCount: course.in_progress_lesson_count,
    })),
    continueLessonSlug: dto.continue_lesson_slug,
    continueLessonTitle: dto.continue_lesson_title,
  };
}

export const learningApi = {
  /** The whole path in one call - every stage, every lesson, nothing locked. */
  async getRoadmap(): Promise<Roadmap> {
    const { data } = await httpClient.get<RoadmapDto>("/learning/roadmap");
    return mapRoadmap(data);
  },

  async getLesson(lessonSlug: string): Promise<Lesson> {
    const { data } = await httpClient.get<LessonDto>(`/learning/lessons/${lessonSlug}`);
    return mapLesson(data);
  },

  async answerQuiz(
    lessonSlug: string,
    stepSlug: string,
    choiceIndex: number,
  ): Promise<QuizAnswerResult> {
    const { data } = await httpClient.post<QuizAnswerResultDto>(
      `/learning/lessons/${lessonSlug}/steps/${stepSlug}/answer`,
      { choice_index: choiceIndex },
    );
    return {
      attemptId: data.attempt_id,
      isCorrect: data.is_correct,
      correctIndex: data.correct_index,
      explanation: data.explanation,
    };
  },

  /**
   * Submits a composition attempt. Deterministic grading always runs;
   * `withAiFeedback` only adds commentary on top of it, and asking for it
   * without an AI available (no key configured, quota spent) is not an
   * error - `aiFeedback` simply comes back `null`.
   */
  async submitComposition(
    lessonSlug: string,
    stepSlug: string,
    document: NotationDocument,
    skillLevel: SkillLevel,
    withAiFeedback: boolean,
  ): Promise<CompositionSubmissionResult> {
    const { data } = await httpClient.post<CompositionSubmissionDto>(
      `/learning/lessons/${lessonSlug}/steps/${stepSlug}/submit`,
      {
        document: notationDocumentToDto(document),
        skill_level: skillLevel,
        with_ai_feedback: withAiFeedback,
      },
    );
    return mapCompositionSubmission(data);
  },

  /** Records that the student reached this step - what starts a lesson. */
  async markStepSeen(lessonSlug: string, stepSlug: string): Promise<StepSeen> {
    const { data } = await httpClient.post<StepSeenDto>(
      `/learning/lessons/${lessonSlug}/steps/${stepSlug}/seen`,
    );
    return {
      lessonId: data.lesson_id,
      currentStepId: data.current_step_id,
      status: data.status,
    };
  },

  async completeLesson(lessonSlug: string): Promise<LessonCompletion> {
    const { data } = await httpClient.post<LessonCompletionDto>(
      `/learning/lessons/${lessonSlug}/complete`,
    );
    return {
      lessonId: data.lesson_id,
      status: data.status,
      completedAt: data.completed_at,
      nextLessonSlug: data.next_lesson_slug,
    };
  },

  async getProgress(): Promise<ProgressSummary> {
    const { data } = await httpClient.get<ProgressSummaryDto>("/learning/progress");
    return mapProgressSummary(data);
  },
};
