<script setup lang="ts">
/**
 * What the skill map's heatmap can't show in one tile: the lessons that
 * teach a topic, the student's own attempt history on it, and drill links
 * out to practice it. Opened by clicking a topic tile in `SkillMapView`.
 */
import { BaseCard } from "@/shared/components/base";

import type { TopicMastery } from "../types";

defineProps<{
  topic: TopicMastery;
}>();

defineEmits<{
  close: [];
}>();
</script>

<template>
  <BaseCard>
    <div class="flex items-start justify-between gap-4">
      <div>
        <h3 class="text-base font-semibold text-slate-900">{{ topic.name }}</h3>
        <p class="mt-1 text-sm text-slate-600">{{ topic.description }}</p>
      </div>
      <button
        type="button"
        class="shrink-0 rounded p-1 text-slate-400 hover:bg-slate-100 hover:text-slate-600"
        aria-label="Close"
        @click="$emit('close')"
      >
        ✕
      </button>
    </div>

    <div class="mt-4">
      <p class="text-xs font-medium uppercase tracking-wide text-slate-400">
        Your attempt history
      </p>
      <p v-if="!topic.recentResults.length" class="mt-2 text-sm text-slate-500">
        No attempts yet.
      </p>
      <div v-else class="mt-2 flex gap-1">
        <span
          v-for="(result, index) in topic.recentResults"
          :key="index"
          class="h-3 w-3 rounded-full"
          :class="result ? 'bg-emerald-500' : 'bg-red-400'"
          :title="result ? 'Correct' : 'Incorrect'"
        />
      </div>
    </div>

    <div class="mt-4">
      <p class="text-xs font-medium uppercase tracking-wide text-slate-400">Taught in</p>
      <p v-if="!topic.lessons.length" class="mt-2 text-sm text-slate-500">
        Not tagged to any lesson yet.
      </p>
      <ul v-else class="mt-2 space-y-1">
        <li v-for="lesson in topic.lessons" :key="lesson.slug">
          <RouterLink
            :to="`/learn/${lesson.slug}`"
            class="text-sm font-medium text-slate-700 hover:text-slate-900 hover:underline"
          >
            {{ lesson.title }} →
          </RouterLink>
        </li>
      </ul>
    </div>
  </BaseCard>
</template>
