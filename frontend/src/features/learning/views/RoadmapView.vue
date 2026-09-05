<script setup lang="ts">
/**
 * The whole path on one page: every stage, every lesson, nothing greyed out.
 *
 * The design decision worth naming is what *isn't* here - no locks, no
 * "complete the previous stage to continue". The roadmap's job is to make
 * the recommended order obvious, and a student who already knows their
 * intervals should be able to jump straight to species counterpoint without
 * arguing with the UI about it.
 */
import { computed, onMounted, ref } from "vue";

import { BaseCard } from "@/shared/components/base";
import { toApiProblem } from "@/shared/utils/api-error";

import LessonCard from "../components/LessonCard.vue";
import ProgressRing from "../components/ProgressRing.vue";
import { useLearningStore } from "../stores/learning.store";

const store = useLearningStore();
const loadError = ref("");

const hasCurriculum = computed(() => (store.roadmap?.courses.length ?? 0) > 0);

const continueSlug = computed(() => store.progress?.continueLessonSlug ?? null);
const continueLesson = computed(() => {
  if (!continueSlug.value || !store.roadmap) return null;
  for (const course of store.roadmap.courses) {
    const found = course.lessons.find((lesson) => lesson.slug === continueSlug.value);
    if (found) return found;
  }
  return null;
});

const levelLabel: Record<string, string> = {
  beginner: "Beginner",
  intermediate: "Intermediate",
  advanced: "Advanced",
};

onMounted(async () => {
  try {
    await Promise.all([store.fetchRoadmap(), store.fetchProgress()]);
  } catch (error) {
    loadError.value = toApiProblem(error).detail ?? "Could not load the roadmap.";
  }
});
</script>

<template>
  <main class="min-h-screen bg-slate-50 px-4 py-10">
    <div class="mx-auto max-w-3xl">
      <header class="mb-8 flex items-start justify-between gap-4">
        <div>
          <h1 class="text-xl font-semibold text-slate-900">Roadmap</h1>
          <p class="mt-1 text-sm text-slate-500">
            Theory and composition, one topic at a time. Work through it in order, or go straight
            to what you need.
          </p>
        </div>
        <RouterLink
          to="/skills"
          class="shrink-0 text-sm font-medium text-slate-600 hover:text-slate-900 hover:underline"
        >
          Skill map →
        </RouterLink>
      </header>

      <p v-if="store.isLoadingRoadmap" class="text-sm text-slate-500">Loading the roadmap…</p>

      <BaseCard v-else-if="loadError">
        <p class="text-sm text-red-600" role="alert">{{ loadError }}</p>
      </BaseCard>

      <BaseCard v-else-if="!hasCurriculum">
        <p class="text-sm text-slate-600">
          No lessons have been published yet. Run
          <code class="rounded bg-slate-100 px-1 py-0.5 font-mono text-xs">
            python -m app.cli seed-curriculum
          </code>
          to load the curriculum.
        </p>
      </BaseCard>

      <template v-else>
        <RouterLink
          v-if="continueLesson"
          :to="`/learn/${continueLesson.slug}`"
          class="mb-8 block rounded-lg border border-slate-900 bg-slate-900 p-5 text-white transition-colors hover:bg-slate-800"
        >
          <p class="text-xs font-medium uppercase tracking-wide text-slate-400">Continue</p>
          <p class="mt-1 text-base font-semibold">{{ continueLesson.title }}</p>
          <p class="mt-0.5 text-sm text-slate-300">{{ continueLesson.summary }}</p>
        </RouterLink>

        <section v-for="course in store.roadmap?.courses ?? []" :key="course.id" class="mb-10">
          <div class="mb-3 flex items-start gap-4">
            <ProgressRing :completed="course.completedLessonCount" :total="course.lessonCount" />
            <div class="min-w-0 flex-1">
              <div class="flex flex-wrap items-baseline gap-x-2">
                <h2 class="text-base font-semibold text-slate-900">{{ course.title }}</h2>
                <span class="text-xs font-medium text-slate-500">
                  {{ levelLabel[course.level] ?? course.level }}
                </span>
              </div>
              <p class="mt-0.5 text-sm text-slate-600">{{ course.description }}</p>
            </div>
          </div>

          <div class="space-y-2">
            <LessonCard
              v-for="(lesson, index) in course.lessons"
              :key="lesson.id"
              :lesson="lesson"
              :index="index"
            />
          </div>
        </section>
      </template>
    </div>
  </main>
</template>
