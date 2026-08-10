<script setup lang="ts">
import { onMounted, ref, watch } from "vue";

import { projectsApi } from "@/features/projects/api/projects.api";
import type { CompositionAnalysis, EngineAnalysis } from "@/features/projects/types";
import { BaseButton, BaseCard } from "@/shared/components/base";
import { toApiProblem } from "@/shared/utils/api-error";

import { feedbackApi } from "../api/feedback.api";
import { SKILL_LEVELS, type Feedback, type SkillLevel } from "../types";
import FeedbackCard from "./FeedbackCard.vue";
import ImprovementSuggestion from "./ImprovementSuggestion.vue";

const props = defineProps<{
  compositionId: string;
}>();

const analysis = ref<CompositionAnalysis | null>(null);
const analysisError = ref("");
const isAnalyzing = ref(true);

const skillLevel = ref<SkillLevel>("intermediate");
const feedback = ref<Feedback | null>(null);
const feedbackError = ref("");
const isLoadingFeedback = ref(false);
const isGeneratingFeedback = ref(false);

const ENGINE_LABELS: Record<"melody" | "harmony" | "rhythm", string> = {
  melody: "Melody",
  harmony: "Harmony",
  rhythm: "Rhythm",
};

async function loadAnalysis(): Promise<void> {
  isAnalyzing.value = true;
  analysisError.value = "";
  try {
    analysis.value = await projectsApi.analyze(props.compositionId);
  } catch (error) {
    analysisError.value = toApiProblem(error).detail ?? "Could not analyze this composition.";
  } finally {
    isAnalyzing.value = false;
  }
}

/** Loads previously generated feedback for the current skill level, if any -
 *  a 404 just means nothing has been generated yet, not a real error. */
async function loadCachedFeedback(): Promise<void> {
  feedback.value = null;
  feedbackError.value = "";
  isLoadingFeedback.value = true;
  try {
    feedback.value = await feedbackApi.get(props.compositionId, skillLevel.value);
  } catch (error) {
    if (toApiProblem(error).status !== 404) {
      feedbackError.value = "Could not load previously generated feedback.";
    }
  } finally {
    isLoadingFeedback.value = false;
  }
}

async function generateFeedback(): Promise<void> {
  feedbackError.value = "";
  isGeneratingFeedback.value = true;
  try {
    feedback.value = await feedbackApi.generate(props.compositionId, skillLevel.value);
  } catch (error) {
    feedbackError.value = toApiProblem(error).detail ?? "Could not generate AI feedback.";
  } finally {
    isGeneratingFeedback.value = false;
  }
}

onMounted(() => {
  void loadAnalysis();
  void loadCachedFeedback();
});

watch(skillLevel, loadCachedFeedback);
</script>

<template>
  <div class="space-y-6">
    <BaseCard title="Analysis">
      <p v-if="isAnalyzing" class="text-sm text-slate-500">Analyzing…</p>
      <p v-else-if="analysisError" class="text-sm text-red-600" role="alert">
        {{ analysisError }}
      </p>
      <template v-else-if="analysis">
        <div class="flex items-baseline gap-3">
          <span class="text-3xl font-semibold text-slate-900">
            {{ analysis.overallScore.toFixed(0) }}
          </span>
          <span class="text-sm text-slate-500">/ 100 overall</span>
        </div>
        <dl class="mt-4 grid grid-cols-3 gap-3">
          <div
            v-for="engine in ['melody', 'harmony', 'rhythm'] as const"
            :key="engine"
            class="rounded-md bg-slate-50 p-3 text-center"
          >
            <dt class="text-xs font-medium uppercase tracking-wide text-slate-500">
              {{ ENGINE_LABELS[engine] }}
            </dt>
            <dd class="mt-1 text-lg font-semibold text-slate-900">
              {{ (analysis[engine] as EngineAnalysis | null)?.score.toFixed(0) ?? "—" }}
            </dd>
          </div>
        </dl>
        <p v-if="analysis.unavailable.length" class="mt-3 text-xs text-slate-500">
          Not scored: {{ analysis.unavailable.map((u) => `${u.engine} (${u.reason})`).join(", ") }}
        </p>
      </template>
    </BaseCard>

    <BaseCard title="AI feedback">
      <div class="flex flex-wrap items-center justify-between gap-3">
        <label class="flex items-center gap-2 text-sm text-slate-700">
          Skill level
          <select
            v-model="skillLevel"
            class="rounded-md border border-slate-300 px-2 py-1 text-sm shadow-sm focus:border-slate-500 focus:outline-none focus:ring-1 focus:ring-slate-500"
          >
            <option v-for="level in SKILL_LEVELS" :key="level" :value="level">
              {{ level }}
            </option>
          </select>
        </label>
        <BaseButton :disabled="isGeneratingFeedback || isAnalyzing" @click="generateFeedback">
          {{
            isGeneratingFeedback
              ? "Generating…"
              : feedback
                ? "Regenerate feedback"
                : "Generate feedback"
          }}
        </BaseButton>
      </div>

      <p v-if="feedbackError" class="mt-4 text-sm text-red-600" role="alert">
        {{ feedbackError }}
      </p>
      <p v-else-if="isLoadingFeedback" class="mt-4 text-sm text-slate-500">Loading feedback…</p>
      <p v-else-if="!feedback && !isGeneratingFeedback" class="mt-4 text-sm text-slate-500">
        No feedback generated yet for this skill level.
      </p>

      <div v-if="feedback" class="mt-4 space-y-6">
        <p class="text-sm text-slate-700">{{ feedback.summary }}</p>

        <section v-if="feedback.strengths.length">
          <h3 class="text-sm font-semibold text-slate-900">Strengths</h3>
          <ul class="mt-2 list-inside list-disc space-y-1 text-sm text-slate-700">
            <li v-for="(strength, index) in feedback.strengths" :key="index">{{ strength }}</li>
          </ul>
        </section>

        <section v-if="feedback.issues.length">
          <h3 class="text-sm font-semibold text-slate-900">Weaknesses</h3>
          <div class="mt-2 space-y-3">
            <FeedbackCard v-for="(issue, index) in feedback.issues" :key="index" :issue="issue" />
          </div>
        </section>

        <section v-if="feedback.suggestions.length">
          <h3 class="text-sm font-semibold text-slate-900">Next steps</h3>
          <div class="mt-2 space-y-2">
            <ImprovementSuggestion
              v-for="(suggestion, index) in feedback.suggestions"
              :key="index"
              :text="suggestion"
            />
          </div>
        </section>
      </div>
    </BaseCard>
  </div>
</template>
