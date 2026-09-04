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

import type {
  Lesson,
  LessonCompletion,
  LessonStep,
  LessonSummary,
  ProgressSummary,
  QuizAnswerResult,
  Roadmap,
  StepSeen,
} from "../types";

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
      requirements: Record<string, unknown>;
      starter_notation: Record<string, unknown> | null;
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
        requirements: dto.requirements,
        starterNotation: dto.starter_notation,
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
