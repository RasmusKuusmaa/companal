import { defineStore } from "pinia";
import { ref } from "vue";

import { examsApi } from "../api/exams.api";
import type { ExamAttemptHistory, ExamSummary } from "../types";

/**
 * Owns the exam list and, per exam, its attempt history - both read many
 * times across the overview, the result view, and the history view, and
 * cheap enough (a handful of exams, a handful of attempts each) that
 * keeping them here avoids every view re-fetching what another just did.
 */
export const useExamsStore = defineStore("exams", () => {
  const exams = ref<ExamSummary[]>([]);
  const isLoadingExams = ref(false);
  const historyByExamSlug = ref<Record<string, ExamAttemptHistory>>({});

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

  return {
    exams,
    isLoadingExams,
    historyByExamSlug,
    fetchExams,
    fetchHistory,
  };
});
