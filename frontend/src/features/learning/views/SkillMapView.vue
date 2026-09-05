<script setup lang="ts">
/**
 * What you've covered, what you're good at, what needs work - in one glance.
 *
 * Grouped by `area` rather than by course: a topic's area ("fundamentals",
 * "harmony", "counterpoint") is the skill map's own axis (see the backend's
 * `Topic` model), and it doesn't always line up one-to-one with a course -
 * several stages can each touch "voice leading" without owning it.
 */
import { computed, onMounted, ref } from "vue";

import { BaseCard } from "@/shared/components/base";
import { toApiProblem } from "@/shared/utils/api-error";

import { useLearningStore } from "../stores/learning.store";
import type { MasteryStatus, TopicMastery } from "../types";

const store = useLearningStore();
const loadError = ref("");

interface AreaGroup {
  area: string;
  topics: TopicMastery[];
}

const areaGroups = computed<AreaGroup[]>(() => {
  const topics = store.skillMap?.topics ?? [];
  const groups: AreaGroup[] = [];
  const byArea = new Map<string, AreaGroup>();
  for (const topic of topics) {
    let group = byArea.get(topic.area);
    if (!group) {
      group = { area: topic.area, topics: [] };
      byArea.set(topic.area, group);
      groups.push(group);
    }
    group.topics.push(topic);
  }
  return groups;
});

const hasTopics = computed(() => (store.skillMap?.topicCount ?? 0) > 0);

function areaLabel(area: string): string {
  return area.replace(/[-_]/g, " ").replace(/\b\w/g, (letter) => letter.toUpperCase());
}

const STATUS_LABEL: Record<MasteryStatus, string> = {
  untouched: "Untouched",
  learning: "Learning",
  solid: "Solid",
  needs_practice: "Needs practice",
};

const STATUS_CLASSES: Record<MasteryStatus, string> = {
  untouched: "border-slate-200 bg-slate-50 text-slate-500",
  learning: "border-sky-200 bg-sky-50 text-sky-700",
  solid: "border-emerald-200 bg-emerald-50 text-emerald-700",
  needs_practice: "border-red-200 bg-red-50 text-red-700",
};

function statusLabel(status: MasteryStatus): string {
  return STATUS_LABEL[status];
}

function statusClasses(status: MasteryStatus): string {
  return STATUS_CLASSES[status];
}

onMounted(async () => {
  try {
    await store.fetchSkillMap();
  } catch (error) {
    loadError.value = toApiProblem(error).detail ?? "Could not load the skill map.";
  }
});
</script>

<template>
  <main class="min-h-screen bg-slate-50 px-4 py-10">
    <div class="mx-auto max-w-3xl">
      <header class="mb-8">
        <h1 class="text-xl font-semibold text-slate-900">Skill map</h1>
        <p class="mt-1 text-sm text-slate-500">
          What you've covered, what you're good at, what needs work.
        </p>
      </header>

      <p v-if="store.isLoadingSkillMap" class="text-sm text-slate-500">Loading the skill map…</p>

      <BaseCard v-else-if="loadError">
        <p class="text-sm text-red-600" role="alert">{{ loadError }}</p>
      </BaseCard>

      <BaseCard v-else-if="!hasTopics">
        <p class="text-sm text-slate-600">
          No topics have been published yet. Run
          <code class="rounded bg-slate-100 px-1 py-0.5 font-mono text-xs">
            python -m app.cli seed-curriculum
          </code>
          to load the curriculum.
        </p>
      </BaseCard>

      <template v-else>
        <p class="mb-8 text-sm text-slate-600">
          {{ store.skillMap?.touchedTopicCount }} of {{ store.skillMap?.topicCount }} topics
          touched.
        </p>

        <section v-for="group in areaGroups" :key="group.area" class="mb-8">
          <h2 class="mb-3 text-base font-semibold text-slate-900">{{ areaLabel(group.area) }}</h2>
          <div class="grid grid-cols-2 gap-2 sm:grid-cols-3">
            <div
              v-for="topic in group.topics"
              :key="topic.id"
              class="rounded-lg border p-3"
              :class="statusClasses(topic.status)"
              :title="topic.description"
            >
              <p class="text-sm font-medium">{{ topic.name }}</p>
              <p class="mt-1 text-xs">
                {{ statusLabel(topic.status) }}
                <template v-if="topic.attemptCount > 0">
                  · {{ Math.round(topic.accuracy * 100) }}%
                </template>
              </p>
            </div>
          </div>
        </section>
      </template>
    </div>
  </main>
</template>
