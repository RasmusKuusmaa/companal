<script setup lang="ts">
/**
 * Every attempt at one exam, side by side, so whether the student is
 * actually improving is visible at a glance rather than buried in a list
 * they have to compare in their head.
 */
import { computed, onMounted, ref } from "vue";
import { useRoute } from "vue-router";

import { BaseButton, BaseCard } from "@/shared/components/base";
import { toApiProblem } from "@/shared/utils/api-error";

import { useExamsStore } from "../stores/exams.store";

const route = useRoute();
const store = useExamsStore();
const loadError = ref("");
const isLoading = ref(true);

const examSlug = computed(() => route.params.examSlug as string);
const history = computed(() => store.historyByExamSlug[examSlug.value] ?? null);
const hasAttempts = computed(() => (history.value?.attempts.length ?? 0) > 0);

function percent(score: number | null, maxScore: number | null): string {
  if (score === null || maxScore === null || maxScore === 0) return "—";
  return `${Math.round((score / maxScore) * 100)}%`;
}

function formatDate(iso: string | null): string {
  if (!iso) return "—";
  return new Date(iso).toLocaleDateString(undefined, {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}

async function load(): Promise<void> {
  loadError.value = "";
  isLoading.value = true;
  try {
    await store.fetchHistory(examSlug.value);
  } catch (error) {
    loadError.value = toApiProblem(error).detail ?? "Could not load this exam's history.";
  } finally {
    isLoading.value = false;
  }
}

onMounted(load);
</script>

<template>
  <main class="min-h-screen bg-slate-50 px-4 py-10">
    <div class="mx-auto max-w-3xl">
      <header class="mb-8 flex items-start justify-between gap-4">
        <div>
          <h1 class="text-xl font-semibold text-slate-900">Attempt history</h1>
          <p class="mt-1 text-sm text-slate-500">{{ examSlug }}</p>
        </div>
        <RouterLink to="/exams" class="text-sm font-medium text-slate-600 hover:text-slate-900">
          All exams →
        </RouterLink>
      </header>

      <p v-if="isLoading" class="text-sm text-slate-500">Loading history…</p>

      <BaseCard v-else-if="loadError">
        <p class="text-sm text-red-600" role="alert">{{ loadError }}</p>
        <div class="mt-4">
          <BaseButton variant="secondary" @click="load">Try again</BaseButton>
        </div>
      </BaseCard>

      <BaseCard v-else-if="!hasAttempts">
        <p class="text-sm text-slate-600">No attempts yet.</p>
      </BaseCard>

      <BaseCard v-else>
        <div class="overflow-x-auto">
          <table class="w-full text-sm">
            <thead>
              <tr
                class="border-b border-slate-200 text-left text-xs uppercase tracking-wide text-slate-500"
              >
                <th class="py-2 pr-4">Attempt</th>
                <th class="py-2 pr-4">Score</th>
                <th class="py-2 pr-4">Percent</th>
                <th class="py-2 pr-4">Started</th>
                <th class="py-2">Status</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="attempt in history?.attempts"
                :key="attempt.attemptId"
                class="border-b border-slate-100 last:border-0"
              >
                <td class="py-2 pr-4 font-medium text-slate-900">#{{ attempt.attemptNumber }}</td>
                <td class="py-2 pr-4 tabular-nums text-slate-700">
                  {{ attempt.score === null ? "—" : `${attempt.score} / ${attempt.maxScore}` }}
                </td>
                <td class="py-2 pr-4 tabular-nums text-slate-700">
                  {{ percent(attempt.score, attempt.maxScore) }}
                </td>
                <td class="py-2 pr-4 text-slate-600">{{ formatDate(attempt.startedAt) }}</td>
                <td class="py-2 text-slate-600">
                  {{ attempt.submittedAt ? "Submitted" : "In progress" }}
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </BaseCard>
    </div>
  </main>
</template>
