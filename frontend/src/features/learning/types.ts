/**
 * Domain types for the roadmap and the lesson player, in the app's camelCase
 * convention. The snake_case wire shapes live in api/learning.api.ts, which
 * is the only place the two are allowed to meet.
 *
 * `LessonStep` is a discriminated union on `kind`, mirroring the backend's
 * own union. Narrowing on `step.kind` is what the player's step components
 * rely on, so adding a step type here means the compiler points at every
 * place that has to handle it.
 */

export type CourseLevel = "beginner" | "intermediate" | "advanced";

export type LessonProgressStatus = "not_started" | "in_progress" | "completed";

export type StepKind = "reading" | "quiz" | "composition";

interface StepBase {
  id: string;
  slug: string;
  position: number;
}

export interface ReadingStep extends StepBase {
  kind: "reading";
  markdown: string;
}

/**
 * Note the absence of an answer key: the API never sends one, and grading
 * happens server-side. The correct choice arrives only in the result of an
 * answer submission.
 */
export interface QuizStep extends StepBase {
  kind: "quiz";
  question: string;
  choices: string[];
}

export interface CompositionStep extends StepBase {
  kind: "composition";
  brief: string;
  requirements: Record<string, unknown>;
  starterNotation: Record<string, unknown> | null;
}

export type LessonStep = ReadingStep | QuizStep | CompositionStep;

export interface LessonSummary {
  id: string;
  slug: string;
  title: string;
  summary: string;
  position: number;
  estimatedMinutes: number;
  stepCount: number;
  status: LessonProgressStatus;
  completedAt: string | null;
}

export interface CourseSummary {
  id: string;
  slug: string;
  title: string;
  description: string;
  level: CourseLevel;
  position: number;
  lessonCount: number;
  completedLessonCount: number;
}

export interface CourseWithLessons extends CourseSummary {
  lessons: LessonSummary[];
}

export interface Roadmap {
  courses: CourseWithLessons[];
  lessonCount: number;
  completedLessonCount: number;
  inProgressLessonCount: number;
}

export interface CourseRef {
  id: string;
  slug: string;
  title: string;
}

export interface Lesson {
  id: string;
  slug: string;
  title: string;
  summary: string;
  position: number;
  estimatedMinutes: number;
  course: CourseRef;
  status: LessonProgressStatus;
  currentStepId: string | null;
  completedAt: string | null;
  steps: LessonStep[];
  previousLessonSlug: string | null;
  nextLessonSlug: string | null;
}

export interface QuizAnswerResult {
  attemptId: string;
  isCorrect: boolean;
  correctIndex: number;
  explanation: string;
}

export interface StepSeen {
  lessonId: string;
  currentStepId: string | null;
  status: LessonProgressStatus;
}

export interface LessonCompletion {
  lessonId: string;
  status: LessonProgressStatus;
  completedAt: string;
  nextLessonSlug: string | null;
}

export interface CourseProgress {
  courseId: string;
  courseSlug: string;
  courseTitle: string;
  lessonCount: number;
  completedLessonCount: number;
  inProgressLessonCount: number;
}

export interface ProgressSummary {
  lessonCount: number;
  completedLessonCount: number;
  inProgressLessonCount: number;
  byCourse: CourseProgress[];
  continueLessonSlug: string | null;
}
