<script setup lang="ts">
/**
 * The dashboard's way back into the roadmap.
 *
 * Reads `/learning/progress` alone rather than the roadmap: the summary
 * carries the resume lesson's slug and title precisely so this card doesn't
 * have to pull the entire curriculum down to render two lines.
 *
 * Failures are silent. This is a convenience on a page that has its own
 * job; an error banner about the learning platform on the compositions
 * dashboard would be noise.
 */
import { computed, onMounted, ref } from "vue";

import { BaseButton, BaseCard } from "@/shared/components/base";

import { useLearningStore } from "../stores/learning.store";

const store = useLearningStore();
const failed = ref(false);

const progress = computed(() => store.progress);
const hasCurriculum = computed(() => (progress.value?.lessonCount ?? 0) > 0);
const percent = computed(() => {
  const summary = progress.value;
  if (!summary || summary.lessonCount === 0) return 0;
  return Math.round((summary.completedLessonCount / summary.lessonCount) * 100);
});

onMounted(async () => {
  try {
    await store.fetchProgress();
  } catch {
    failed.value = true;
  }
});
</script>

<template>
  <BaseCard v-if="!failed && hasCurriculum">
    <div class="flex flex-wrap items-start justify-between gap-4">
      <div class="min-w-0 flex-1">
        <h2 class="text-base font-semibold text-slate-900">Learning</h2>

        <p v-if="progress?.continueLessonTitle" class="mt-1 text-sm text-slate-600">
          Next up:
          <span class="font-medium text-slate-900">{{ progress.continueLessonTitle }}</span>
        </p>
        <p v-else class="mt-1 text-sm text-slate-600">
          You've finished every lesson on the roadmap.
        </p>

        <div class="mt-3 flex items-center gap-3">
          <div class="h-1.5 w-40 overflow-hidden rounded-full bg-slate-200">
            <div
              class="h-full rounded-full bg-slate-900 transition-all duration-300"
              :style="{ width: `${percent}%` }"
            />
          </div>
          <span class="text-xs font-medium tabular-nums text-slate-500">
            {{ progress?.completedLessonCount ?? 0 }} / {{ progress?.lessonCount ?? 0 }} lessons
          </span>
        </div>
      </div>

      <RouterLink
        :to="progress?.continueLessonSlug ? `/learn/${progress.continueLessonSlug}` : '/learn'"
      >
        <BaseButton>{{ progress?.continueLessonSlug ? "Continue" : "Roadmap" }}</BaseButton>
      </RouterLink>
    </div>
  </BaseCard>
</template>
