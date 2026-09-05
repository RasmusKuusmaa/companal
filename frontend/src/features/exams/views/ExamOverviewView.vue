<script setup lang="ts">
/**
 * Every exam in one place: what it covers, how you've done on it before,
 * and a way to start another attempt. Past attempts are fetched per exam
 * (one request each) rather than added to the list endpoint - the exam
 * list is a handful of rows, so the extra round trips cost nothing and
 * keep `ExamSummary` itself free of per-student data.
 */
import { computed, onMounted, ref } from "vue";

import { BaseButton, BaseCard } from "@/shared/components/base";
import { toApiProblem } from "@/shared/utils/api-error";

import { useExamsStore } from "../stores/exams.store";

const store = useExamsStore();
const loadError = ref("");

const hasExams = computed(() => store.exams.length > 0);

function scopeLabel(courseSlug: string | null): string {
  if (!courseSlug) return "Comprehensive final";
  return courseSlug.replace(/[-_]/g, " ").replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function attemptsLabel(examSlug: string): string {
  const history = store.historyByExamSlug[examSlug];
  if (!history || history.attempts.length === 0) return "Not attempted yet";

  const graded = history.attempts.filter((attempt) => attempt.score !== null);
  if (graded.length === 0) {
    return `${history.attempts.length} ${history.attempts.length === 1 ? "attempt" : "attempts"} in progress`;
  }

  const best = graded.reduce((max, attempt) => Math.max(max, attempt.score ?? 0), 0);
  const bestMax = graded.find((attempt) => attempt.score === best)?.maxScore ?? 0;
  return `${history.attempts.length} ${history.attempts.length === 1 ? "attempt" : "attempts"} · best ${best}/${bestMax}`;
}

function hasHistory(examSlug: string): boolean {
  return (store.historyByExamSlug[examSlug]?.attempts.length ?? 0) > 0;
}

async function load(): Promise<void> {
  loadError.value = "";
  try {
    await store.fetchExams();
    await Promise.all(store.exams.map((exam) => store.fetchHistory(exam.slug)));
  } catch (error) {
    loadError.value = toApiProblem(error).detail ?? "Could not load the exams.";
  }
}

onMounted(load);
</script>

<template>
  <main class="min-h-screen bg-slate-50 px-4 py-10">
    <div class="mx-auto max-w-3xl">
      <header class="mb-8">
        <h1 class="text-xl font-semibold text-slate-900">Exams</h1>
        <p class="mt-1 text-sm text-slate-500">
          One per stage, plus a comprehensive final. Retake as often as you like - every attempt is
          kept and graded.
        </p>
      </header>

      <p v-if="store.isLoadingExams" class="text-sm text-slate-500">Loading exams…</p>

      <BaseCard v-else-if="loadError">
        <p class="text-sm text-red-600" role="alert">{{ loadError }}</p>
        <div class="mt-4">
          <BaseButton variant="secondary" @click="load">Try again</BaseButton>
        </div>
      </BaseCard>

      <BaseCard v-else-if="!hasExams">
        <p class="text-sm text-slate-600">
          No exams have been published yet. Run
          <code class="rounded bg-slate-100 px-1 py-0.5 font-mono text-xs">
            python -m app.cli seed-curriculum
          </code>
          to load the curriculum.
        </p>
      </BaseCard>

      <div v-else class="space-y-3">
        <BaseCard v-for="exam in store.exams" :key="exam.id">
          <div class="flex flex-wrap items-start justify-between gap-4">
            <div class="min-w-0 flex-1">
              <div class="flex flex-wrap items-baseline gap-x-2">
                <h2 class="text-base font-semibold text-slate-900">{{ exam.title }}</h2>
                <span class="text-xs font-medium text-slate-500">{{
                  scopeLabel(exam.courseSlug)
                }}</span>
              </div>
              <p class="mt-1 text-sm text-slate-600">{{ exam.description }}</p>
              <p class="mt-2 text-xs text-slate-500">{{ attemptsLabel(exam.slug) }}</p>
            </div>

            <div class="flex shrink-0 items-center gap-2">
              <RouterLink v-if="hasHistory(exam.slug)" :to="`/exams/${exam.slug}/history`">
                <BaseButton variant="ghost">History</BaseButton>
              </RouterLink>
              <RouterLink :to="`/exams/${exam.slug}/attempt`">
                <BaseButton>Start</BaseButton>
              </RouterLink>
            </div>
          </div>
        </BaseCard>
      </div>
    </div>
  </main>
</template>
