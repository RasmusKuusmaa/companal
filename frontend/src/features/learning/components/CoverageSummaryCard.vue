<script setup lang="ts">
/**
 * The dashboard's one-line answer to "how am I doing overall" - how much of
 * the curriculum has been touched, and how that touched slice splits by
 * mastery. Same silent-failure convention as `ContinueLearningCard`: this
 * is a convenience on a page with its own job, not somewhere that should
 * ever show an error banner about the learning platform.
 */
import { computed, onMounted, ref } from "vue";

import { BaseButton, BaseCard } from "@/shared/components/base";

import { useLearningStore } from "../stores/learning.store";
import type { MasteryStatus } from "../types";

type TouchedStatus = Exclude<MasteryStatus, "untouched">;

const STATUS_LABEL: Record<TouchedStatus, string> = {
  learning: "learning",
  solid: "solid",
  needs_practice: "needs practice",
};

const STATUS_DOT_CLASSES: Record<TouchedStatus, string> = {
  learning: "bg-sky-500",
  solid: "bg-emerald-500",
  needs_practice: "bg-red-500",
};

const store = useLearningStore();
const failed = ref(false);

const skillMap = computed(() => store.skillMap);
const hasTopics = computed(() => (skillMap.value?.topicCount ?? 0) > 0);

const masterySplit = computed(() => {
  const counts: Record<TouchedStatus, number> = { learning: 0, solid: 0, needs_practice: 0 };
  for (const topic of skillMap.value?.topics ?? []) {
    if (topic.status === "untouched") continue;
    counts[topic.status] += 1;
  }
  return (Object.keys(counts) as TouchedStatus[])
    .filter((status) => counts[status] > 0)
    .map((status) => ({ status, count: counts[status] }));
});

onMounted(async () => {
  try {
    await store.fetchSkillMap();
  } catch {
    failed.value = true;
  }
});
</script>

<template>
  <BaseCard v-if="!failed && hasTopics">
    <div class="flex flex-wrap items-start justify-between gap-4">
      <div class="min-w-0 flex-1">
        <h2 class="text-base font-semibold text-slate-900">Skill coverage</h2>
        <p class="mt-1 text-sm text-slate-600">
          {{ skillMap?.touchedTopicCount }} of {{ skillMap?.topicCount }} topics touched
        </p>

        <div v-if="masterySplit.length" class="mt-3 flex flex-wrap gap-3">
          <span
            v-for="entry in masterySplit"
            :key="entry.status"
            class="flex items-center gap-1.5 text-xs font-medium text-slate-600"
          >
            <span class="h-2 w-2 rounded-full" :class="STATUS_DOT_CLASSES[entry.status]" />
            {{ entry.count }} {{ STATUS_LABEL[entry.status] }}
          </span>
        </div>
      </div>

      <RouterLink to="/skills">
        <BaseButton variant="ghost">Skill map</BaseButton>
      </RouterLink>
    </div>
  </BaseCard>
</template>
