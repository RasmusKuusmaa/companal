import { defineStore } from "pinia";
import { ref } from "vue";

import type { SkillLevel } from "@/features/feedback/types";

import { examsApi } from "../api/exams.api";
import type {
  ExamAnswerPayload,
  ExamAttemptHistory,
  ExamAttemptResult,
  ExamAttemptStart,
  ExamSummary,
} from "../types";

/**
 * Owns the exam list and, per exam, its attempt history - both read many
 * times across the overview, the result view, and the history view, and
 * cheap enough (a handful of exams, a handful of attempts each) that
 * keeping them here avoids every view re-fetching what another just did.
 *
 * It also owns whichever attempt is currently being taken. `attemptResult`
 * is session-scoped rather than re-fetchable - there is no endpoint that
 * hands back one attempt's full per-question breakdown after the fact,
 * only the summaries `fetchHistory` reads - so the result view can only
 * show a fresh submission, not one reloaded from a bookmark.
 */
export const useExamsStore = defineStore("exams", () => {
  const exams = ref<ExamSummary[]>([]);
  const isLoadingExams = ref(false);
  const historyByExamSlug = ref<Record<string, ExamAttemptHistory>>({});

  const currentAttempt = ref<ExamAttemptStart | null>(null);
  const isStartingAttempt = ref(false);
  const heldAnswers = ref<Record<string, ExamAnswerPayload>>({});
  const attemptResult = ref<ExamAttemptResult | null>(null);
  const isSubmittingAttempt = ref(false);

  async function fetchExams(): Promise<void> {
    isLoadingExams.value = true;
    try {
      exams.value = await examsApi.listExams();
    } finally {
      isLoadingExams.value = false;
    }
  }

  async function fetchHistory(examSlug: string): Promise<ExamAttemptHistory> {
    const history = await examsApi.getAttemptHistory(examSlug);
    historyByExamSlug.value = { ...historyByExamSlug.value, [examSlug]: history };
    return history;
  }

  /** Starts a fresh attempt - always a new one, never a resume (see the
   *  backend's `start_attempt`), so any answers held for an earlier
   *  attempt at this exam are irrelevant and cleared here too. */
  async function startAttempt(examSlug: string): Promise<ExamAttemptStart> {
    isStartingAttempt.value = true;
    try {
      currentAttempt.value = await examsApi.startAttempt(examSlug);
      heldAnswers.value = {};
      attemptResult.value = null;
      return currentAttempt.value;
    } finally {
      isStartingAttempt.value = false;
    }
  }

  /** Holds one answer against the current attempt. Nothing is graded until
   *  `submitAttempt` - see the backend's `answer_question`. */
  async function holdAnswer(questionId: string, answer: ExamAnswerPayload): Promise<void> {
    const attempt = currentAttempt.value;
    if (!attempt) throw new Error("No attempt is in progress.");
    await examsApi.answerQuestion(attempt.attemptId, questionId, answer);
    heldAnswers.value = { ...heldAnswers.value, [questionId]: answer };
  }

  async function submitAttempt(
    withAiFeedback: boolean,
    skillLevel: SkillLevel,
  ): Promise<ExamAttemptResult> {
    const attempt = currentAttempt.value;
    if (!attempt) throw new Error("No attempt is in progress.");
    isSubmittingAttempt.value = true;
    try {
      attemptResult.value = await examsApi.submitAttempt(
        attempt.attemptId,
        withAiFeedback,
        skillLevel,
      );
      return attemptResult.value;
    } finally {
      isSubmittingAttempt.value = false;
    }
  }

  return {
    exams,
    isLoadingExams,
    historyByExamSlug,
    currentAttempt,
    isStartingAttempt,
    heldAnswers,
    attemptResult,
    isSubmittingAttempt,
    fetchExams,
    fetchHistory,
    startAttempt,
    holdAnswer,
    submitAttempt,
  };
});
