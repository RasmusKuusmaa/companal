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

import TopicDetailPanel from "../components/TopicDetailPanel.vue";
import { useLearningStore } from "../stores/learning.store";
import type { MasteryStatus, TopicMastery } from "../types";

const store = useLearningStore();
const loadError = ref("");
const selectedTopicSlug = ref<string | null>(null);
const selectedTopic = computed(() =>
  (store.skillMap?.topics ?? []).find((topic) => topic.slug === selectedTopicSlug.value) ?? null,
);

function selectTopic(slug: string): void {
  selectedTopicSlug.value = selectedTopicSlug.value === slug ? null : slug;
}

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

/**
 * The explicit answer to "what should I work on" - `needsPractice` sorted
 * worst-first is the priority list, `strengths` best-first is the reward
 * for having got there. Both read straight off `status`, the same
 * classification the heatmap colors by, so this list and the map never
 * disagree about where a topic stands.
 */
const needsPractice = computed(() =>
  (store.skillMap?.topics ?? [])
    .filter((topic) => topic.status === "needs_practice")
    .sort((a, b) => a.accuracy - b.accuracy),
);

const strengths = computed(() =>
  (store.skillMap?.topics ?? [])
    .filter((topic) => topic.status === "solid")
    .sort((a, b) => b.accuracy - a.accuracy),
);

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

        <TopicDetailPanel
          v-if="selectedTopic"
          :topic="selectedTopic"
          class="mb-8"
          @close="selectedTopicSlug = null"
        />

        <div v-if="needsPractice.length || strengths.length" class="mb-8 grid gap-4 sm:grid-cols-2">
          <BaseCard title="Needs practice">
            <p v-if="!needsPractice.length" class="text-sm text-slate-500">
              Nothing flagged right now.
            </p>
            <ul v-else class="space-y-2">
              <li
                v-for="topic in needsPractice"
                :key="topic.id"
                class="flex items-center justify-between gap-2 text-sm"
              >
                <span class="text-slate-900">{{ topic.name }}</span>
                <RouterLink
                  v-if="topic.lessons[0]"
                  :to="`/learn/${topic.lessons[0].slug}`"
                  class="shrink-0 text-xs font-medium text-slate-500 hover:text-slate-900"
                >
                  Practice →
                </RouterLink>
              </li>
            </ul>
          </BaseCard>

          <BaseCard title="Strengths">
            <p v-if="!strengths.length" class="text-sm text-slate-500">
              Nothing solid yet - keep going.
            </p>
            <ul v-else class="space-y-2">
              <li
                v-for="topic in strengths"
                :key="topic.id"
                class="flex items-center justify-between gap-2 text-sm"
              >
                <span class="text-slate-900">{{ topic.name }}</span>
                <span class="shrink-0 text-xs text-slate-500">
                  {{ Math.round(topic.accuracy * 100) }}%
                </span>
              </li>
            </ul>
          </BaseCard>
        </div>

        <section v-for="group in areaGroups" :key="group.area" class="mb-8">
          <h2 class="mb-3 text-base font-semibold text-slate-900">{{ areaLabel(group.area) }}</h2>
          <div class="grid grid-cols-2 gap-2 sm:grid-cols-3">
            <button
              v-for="topic in group.topics"
              :key="topic.id"
              type="button"
              class="rounded-lg border p-3 text-left transition-shadow hover:shadow-sm"
              :class="statusClasses(topic.status)"
              :title="topic.description"
              @click="selectTopic(topic.slug)"
            >
              <p class="text-sm font-medium">{{ topic.name }}</p>
              <p class="mt-1 text-xs">
                {{ statusLabel(topic.status) }}
                <template v-if="topic.attemptCount > 0">
                  · {{ Math.round(topic.accuracy * 100) }}%
                </template>
              </p>
            </button>
          </div>
        </section>
      </template>
    </div>
  </main>
</template>
