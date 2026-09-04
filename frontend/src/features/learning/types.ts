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

import type { FeedbackIssue, SkillLevel } from "@/features/feedback/types";
import type { NotationDocument } from "@/features/notation/types";

export type { SkillLevel };

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

export type CadenceKind =
  "perfect_authentic" | "imperfect_authentic" | "half" | "plagal" | "deceptive";

/**
 * The declarative rule language a composition brief is stated in - mirrors
 * `app.domains.notation.requirements` on the backend, which is the only
 * place any of these are actually checked. `type` is the discriminator,
 * shared verbatim with the backend the same way `StepKind` is.
 */
export type Requirement =
  | { type: "key"; key: string }
  | { type: "time_signature"; value: string }
  | { type: "measure_count"; count: number }
  | { type: "cadence"; cadence: CadenceKind }
  | { type: "range"; maxSemitones: number | null; lowest: string | null; highest: string | null }
  | { type: "max_leap"; semitones: number }
  | { type: "leap_recovery"; maxUnresolved: number }
  | { type: "diatonic_only" }
  | { type: "required_scale_degrees"; degrees: number[] }
  | { type: "forbidden_pitches"; pitches: string[] };

export interface CompositionStep extends StepBase {
  kind: "composition";
  brief: string;
  requirements: Requirement[];
  /** A given soprano, bass or cantus firmus the student writes against. */
  starterNotation: NotationDocument | null;
  /** Indices into `starterNotation.staves` the student can't edit. */
  lockedStaffIndices: number[];
}

export type LessonStep = ReadingStep | QuizStep | CompositionStep;

/** The verdict on one requirement, for the checklist a student sees. */
export interface RequirementResult {
  requirement: Requirement;
  passed: boolean;
  message: string;
  measure: number | null;
}

/**
 * The AI teacher's commentary on one exercise submission - the same shape
 * as a composition's stored `Feedback`, minus the metadata (id, skill
 * level, timestamps) that only applies to a *stored* row. This one rides
 * along with a single submission and is never fetched again on its own.
 */
export interface CompositionAiFeedback {
  summary: string;
  strengths: string[];
  issues: FeedbackIssue[];
  suggestions: string[];
}

/**
 * A graded composition submission. Deterministic grading (`requirementResults`,
 * `passed`) is always present; `aiFeedback` rides along only when requested
 * and available - see `CompositionStep.vue` for what "unavailable" looks
 * like to a student.
 */
export interface CompositionSubmissionResult {
  attemptId: string;
  createdAt: string;
  requirementResults: RequirementResult[];
  passed: boolean;
  overallScore: number | null;
  aiFeedback: CompositionAiFeedback | null;
}

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
  continueLessonTitle: string | null;
}
