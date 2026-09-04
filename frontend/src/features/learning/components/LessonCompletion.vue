<script setup lang="ts">
/**
 * The end of a lesson: finish it, then go somewhere sensible.
 *
 * Finishing is a button the student presses, not something inferred from
 * reaching the last step. Scrolling to the bottom of a page isn't the same
 * as having understood it, and a student who wants to leave a lesson open
 * and come back to it shouldn't find it silently marked done.
 *
 * Nothing is required to finish - a failed check doesn't block it. The
 * attempts are recorded regardless, and the skill map is where weak topics
 * surface, rather than a gate on the lesson itself.
 */
import { computed, ref } from "vue";
import { useRouter } from "vue-router";

import { BaseButton } from "@/shared/components/base";
import { toApiProblem } from "@/shared/utils/api-error";

import { useLearningStore } from "../stores/learning.store";

const router = useRouter();
const store = useLearningStore();

const isSaving = ref(false);
const saveError = ref("");

const isCompleted = computed(() => store.lesson?.status === "completed");
const nextSlug = computed(() => store.lesson?.nextLessonSlug ?? null);

/** The next lesson's title, if the roadmap happens to be loaded. */
const nextTitle = computed(() => {
  if (!nextSlug.value || !store.roadmap) return null;
  for (const course of store.roadmap.courses) {
    const found = course.lessons.find((lesson) => lesson.slug === nextSlug.value);
    if (found) return found.title;
  }
  return null;
});

async function finish(): Promise<void> {
  if (isSaving.value) return;
  isSaving.value = true;
  saveError.value = "";
  try {
    await store.completeLesson();
  } catch (error) {
    saveError.value = toApiProblem(error).detail ?? "Could not save your progress.";
  } finally {
    isSaving.value = false;
  }
}

async function goToNext(): Promise<void> {
  if (nextSlug.value) await router.push(`/learn/${nextSlug.value}`);
}
</script>

<template>
  <section class="mt-6 rounded-lg border border-slate-200 bg-white p-6">
    <template v-if="!isCompleted">
      <h3 class="text-base font-semibold text-slate-900">That's the end of this lesson</h3>
      <p class="mt-1 text-sm text-slate-600">
        Mark it complete when you're happy with it. You can come back and re-read it any time.
      </p>
      <p v-if="saveError" class="mt-3 text-sm text-red-600" role="alert">{{ saveError }}</p>
      <div class="mt-4">
        <BaseButton :disabled="isSaving" @click="finish">
          {{ isSaving ? "Saving…" : "Mark lesson complete" }}
        </BaseButton>
      </div>
    </template>

    <template v-else>
      <div class="flex items-start gap-3">
        <span
          class="mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-emerald-600 text-white"
        >
          <svg class="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
            <path
              fill-rule="evenodd"
              d="M16.7 5.3a1 1 0 0 1 0 1.4l-7.5 7.5a1 1 0 0 1-1.4 0l-3.5-3.5a1 1 0 1 1 1.4-1.4l2.8 2.8 6.8-6.8a1 1 0 0 1 1.4 0Z"
              clip-rule="evenodd"
            />
          </svg>
        </span>
        <div class="min-w-0 flex-1">
          <h3 class="text-base font-semibold text-slate-900">Lesson complete</h3>
          <p v-if="nextTitle" class="mt-1 text-sm text-slate-600">Up next: {{ nextTitle }}</p>
          <p v-else-if="!nextSlug" class="mt-1 text-sm text-slate-600">
            That's the last lesson on the roadmap.
          </p>
        </div>
      </div>

      <div class="mt-5 flex flex-wrap gap-2">
        <BaseButton v-if="nextSlug" @click="goToNext">Next lesson</BaseButton>
        <RouterLink to="/learn">
          <BaseButton variant="secondary">Back to the roadmap</BaseButton>
        </RouterLink>
      </div>
    </template>
  </section>
</template>
