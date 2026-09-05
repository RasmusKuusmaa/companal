<script setup lang="ts">
/**
 * The verdict on a just-submitted attempt: score, then every question's own
 * breakdown, then a way to go work on whatever it exposed.
 *
 * `store.attemptResult` is session state, not something this view can
 * re-fetch - see `exams.store`'s own docstring - so landing here without
 * having just submitted (a refresh, a bookmark) has nothing to show but a
 * way back to the exam list. Question text/choices/brief aren't part of
 * the result either; they're read from `store.currentAttempt.exam`, the
 * same in-memory exam the runner just finished with.
 *
 * "Links to weak topics" doesn't point at a specific topic per question -
 * an exam question isn't tagged to one the way a lesson step is (see
 * `exams.models.ExamQuestion`) - so a less-than-perfect score links to the
 * skill map instead, which is exactly where "what should I work on" is
 * already answered.
 */
import { computed } from "vue";

import { BaseButton, BaseCard } from "@/shared/components/base";

import { useExamsStore } from "../stores/exams.store";
import type { ExamCompositionQuestion, ExamQuestion, ExamQuizQuestion } from "../types";

const store = useExamsStore();

const result = computed(() => store.attemptResult);
const exam = computed(() => store.currentAttempt?.exam ?? null);

const percent = computed(() => {
  const current = result.value;
  if (!current || current.maxScore === 0) return 0;
  return Math.round((current.score / current.maxScore) * 100);
});

const isPerfect = computed(() => {
  const current = result.value;
  return current !== null && current.maxScore > 0 && current.score === current.maxScore;
});

function questionFor(questionId: string): ExamQuestion | null {
  return exam.value?.questions.find((question) => question.id === questionId) ?? null;
}

interface RequirementResultDetail {
  passed: boolean;
  message: string;
  measure: number | null;
}

function requirementResults(detail: Record<string, unknown>): RequirementResultDetail[] {
  const raw = detail.requirement_results;
  return Array.isArray(raw) ? (raw as RequirementResultDetail[]) : [];
}
</script>

<template>
  <main class="min-h-screen bg-slate-50 px-4 py-10">
    <div class="mx-auto max-w-3xl">
      <BaseCard v-if="!result">
        <p class="text-sm text-slate-600">
          There's no fresh result to show here - results are only visible right after submitting.
        </p>
        <RouterLink to="/exams" class="mt-4 inline-block">
          <BaseButton variant="ghost">Back to exams</BaseButton>
        </RouterLink>
      </BaseCard>

      <template v-else>
        <header class="mb-8">
          <h1 class="text-xl font-semibold text-slate-900">
            {{ exam?.title ?? "Exam result" }}
          </h1>
          <p class="mt-1 text-sm text-slate-500">Attempt {{ result.attemptNumber }}</p>
        </header>

        <BaseCard class="mb-8">
          <p
            class="text-sm font-semibold"
            :class="isPerfect ? 'text-emerald-700' : 'text-slate-900'"
          >
            {{ result.score }} / {{ result.maxScore }} ({{ percent }}%)
          </p>
        </BaseCard>

        <div class="space-y-4">
          <BaseCard
            v-for="questionResult in result.questionResults"
            :key="questionResult.questionId"
          >
            <template v-if="questionResult.kind === 'quiz'">
              <p class="text-sm font-semibold text-slate-900">
                {{ (questionFor(questionResult.questionId) as ExamQuizQuestion | null)?.question }}
              </p>
              <p
                class="mt-2 text-sm font-medium"
                :class="questionResult.detail.is_correct ? 'text-emerald-700' : 'text-red-700'"
              >
                {{ questionResult.detail.is_correct ? "Correct." : "Not quite." }}
              </p>
              <p class="mt-2 text-sm text-slate-600">{{ questionResult.detail.explanation }}</p>
            </template>

            <template v-else>
              <p class="text-sm text-slate-800">
                {{
                  (questionFor(questionResult.questionId) as ExamCompositionQuestion | null)?.brief
                }}
              </p>
              <p
                class="mt-2 text-sm font-medium"
                :class="questionResult.detail.passed ? 'text-emerald-700' : 'text-red-700'"
              >
                {{
                  questionResult.detail.passed ? "Every requirement met." : "Not quite there yet."
                }}
              </p>
              <ul class="mt-2 space-y-1 text-sm">
                <li
                  v-for="(item, index) in requirementResults(questionResult.detail)"
                  :key="index"
                  class="flex items-start gap-2"
                >
                  <span :class="item.passed ? 'text-emerald-600' : 'text-red-600'">
                    {{ item.passed ? "✓" : "✗" }}
                  </span>
                  <span :class="item.passed ? 'text-slate-700' : 'text-slate-900'">
                    {{ item.message }}
                  </span>
                </li>
              </ul>
            </template>
          </BaseCard>
        </div>

        <div class="mt-8 flex flex-wrap gap-3">
          <RouterLink v-if="!isPerfect" to="/skills">
            <BaseButton>Review your skill map</BaseButton>
          </RouterLink>
          <RouterLink to="/exams">
            <BaseButton variant="ghost">Back to exams</BaseButton>
          </RouterLink>
        </div>
      </template>
    </div>
  </main>
</template>
