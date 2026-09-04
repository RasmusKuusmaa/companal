import { defineStore } from "pinia";
import { computed, ref } from "vue";

import { learningApi } from "../api/learning.api";
import type {
  Lesson,
  LessonProgressStatus,
  LessonStep,
  ProgressSummary,
  QuizAnswerResult,
  Roadmap,
} from "../types";

/**
 * Owns the roadmap and whichever lesson is open.
 *
 * Both live here rather than in the views because they have to agree: when
 * a lesson is completed the roadmap card behind it should already say so
 * when the student navigates back, without a refetch. `applyLessonStatus`
 * is that reconciliation, and it's why completion goes through the store
 * instead of the API module directly.
 *
 * Quiz results are held per step slug, not per step, so a student who
 * answers, moves on, and comes back still sees the explanation they were
 * given. They're cleared when a different lesson opens - they belong to the
 * session with that lesson, not to the account.
 */
export const useLearningStore = defineStore("learning", () => {
  const roadmap = ref<Roadmap | null>(null);
  const progress = ref<ProgressSummary | null>(null);
  const lesson = ref<Lesson | null>(null);
  const stepIndex = ref(0);
  const quizResults = ref<Record<string, QuizAnswerResult>>({});

  const isLoadingRoadmap = ref(false);
  const isLoadingLesson = ref(false);

  const steps = computed<LessonStep[]>(() => lesson.value?.steps ?? []);
  const currentStep = computed<LessonStep | null>(() => steps.value[stepIndex.value] ?? null);
  const isFirstStep = computed(() => stepIndex.value === 0);
  const isLastStep = computed(
    () => steps.value.length > 0 && stepIndex.value === steps.value.length - 1,
  );

  function applyLessonStatus(
    lessonSlug: string,
    status: LessonProgressStatus,
    completedAt: string | null,
  ): void {
    if (!roadmap.value) return;

    let completed = 0;
    let inProgress = 0;
    for (const course of roadmap.value.courses) {
      let completedHere = 0;
      for (const summary of course.lessons) {
        if (summary.slug === lessonSlug) {
          summary.status = status;
          summary.completedAt = completedAt;
        }
        if (summary.status === "completed") completedHere += 1;
        if (summary.status === "in_progress") inProgress += 1;
      }
      course.completedLessonCount = completedHere;
      completed += completedHere;
    }
    roadmap.value.completedLessonCount = completed;
    roadmap.value.inProgressLessonCount = inProgress;
  }

  async function fetchRoadmap(): Promise<void> {
    isLoadingRoadmap.value = true;
    try {
      roadmap.value = await learningApi.getRoadmap();
    } finally {
      isLoadingRoadmap.value = false;
    }
  }

  async function fetchProgress(): Promise<void> {
    progress.value = await learningApi.getProgress();
  }

  /** Opens a lesson, resuming at the step the student last reached. */
  async function openLesson(lessonSlug: string): Promise<Lesson> {
    isLoadingLesson.value = true;
    try {
      const loaded = await learningApi.getLesson(lessonSlug);
      lesson.value = loaded;
      quizResults.value = {};

      const resumeAt = loaded.steps.findIndex((step) => step.id === loaded.currentStepId);
      stepIndex.value = resumeAt >= 0 ? resumeAt : 0;
      return loaded;
    } finally {
      isLoadingLesson.value = false;
    }
  }

  function goToStep(index: number): void {
    if (index < 0 || index >= steps.value.length) return;
    stepIndex.value = index;
  }

  function nextStep(): void {
    goToStep(stepIndex.value + 1);
  }

  function previousStep(): void {
    goToStep(stepIndex.value - 1);
  }

  /**
   * Tells the backend the student reached this step. Failures are swallowed
   * on purpose: this is bookkeeping, and a dropped request should not stop
   * someone reading the lesson in front of them.
   */
  async function markSeen(stepSlug: string): Promise<void> {
    const open = lesson.value;
    if (!open) return;
    try {
      const seen = await learningApi.markStepSeen(open.slug, stepSlug);
      open.currentStepId = seen.currentStepId;
      if (open.status === "not_started") {
        open.status = seen.status;
        applyLessonStatus(open.slug, seen.status, null);
      }
    } catch {
      // Bookkeeping only - see above.
    }
  }

  async function answerQuiz(stepSlug: string, choiceIndex: number): Promise<QuizAnswerResult> {
    const open = lesson.value;
    if (!open) throw new Error("No lesson is open.");

    const result = await learningApi.answerQuiz(open.slug, stepSlug, choiceIndex);
    quizResults.value = { ...quizResults.value, [stepSlug]: result };
    if (open.status === "not_started") {
      open.status = "in_progress";
      applyLessonStatus(open.slug, "in_progress", null);
    }
    return result;
  }

  /** Clears a stored result so the student can answer the question again. */
  function retryQuiz(stepSlug: string): void {
    const rest = { ...quizResults.value };
    delete rest[stepSlug];
    quizResults.value = rest;
  }

  async function completeLesson(): Promise<string | null> {
    const open = lesson.value;
    if (!open) throw new Error("No lesson is open.");

    const completion = await learningApi.completeLesson(open.slug);
    open.status = completion.status;
    open.completedAt = completion.completedAt;
    applyLessonStatus(open.slug, completion.status, completion.completedAt);
    return completion.nextLessonSlug;
  }

  return {
    roadmap,
    progress,
    lesson,
    stepIndex,
    quizResults,
    isLoadingRoadmap,
    isLoadingLesson,
    steps,
    currentStep,
    isFirstStep,
    isLastStep,
    fetchRoadmap,
    fetchProgress,
    openLesson,
    goToStep,
    nextStep,
    previousStep,
    markSeen,
    answerQuiz,
    retryQuiz,
    completeLesson,
  };
});
