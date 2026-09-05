<script setup lang="ts">
/**
 * The lesson player: one step at a time, in order.
 *
 * A lesson is a list of steps of different kinds, so this is a stepper
 * rather than a page - read a passage, answer a check on what you just
 * read, write something, move on. Reaching a step reports it to the
 * backend, which is what makes "continue where you left off" work and what
 * moves a lesson out of `not_started`.
 *
 * Navigation is never blocked on getting a question right. A student can
 * move past a check they failed; the attempt is recorded either way, and
 * the skill map is where being repeatedly wrong actually shows up.
 */
import { computed, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";

import { BaseButton, BaseCard } from "@/shared/components/base";
import { toApiProblem } from "@/shared/utils/api-error";

import CompositionStep from "../components/CompositionStep.vue";
import LessonCompletion from "../components/LessonCompletion.vue";
import MultipleChoiceStep from "../components/MultipleChoiceStep.vue";
import ReadingStep from "../components/ReadingStep.vue";
import { useLearningStore } from "../stores/learning.store";

const route = useRoute();
const router = useRouter();
const store = useLearningStore();

const loadError = ref("");

const lessonSlug = computed(() => String(route.params.lessonSlug ?? ""));
const stepNumber = computed(() => store.stepIndex + 1);
const stepTotal = computed(() => store.steps.length);
const percent = computed(() =>
  stepTotal.value === 0 ? 0 : Math.round((stepNumber.value / stepTotal.value) * 100),
);

async function load(slug: string): Promise<void> {
  loadError.value = "";
  try {
    await store.openLesson(slug);
    const step = store.currentStep;
    if (step) void store.markSeen(step.slug);
  } catch (error) {
    const problem = toApiProblem(error);
    loadError.value =
      problem.status === 404
        ? "That lesson doesn't exist."
        : (problem.detail ?? "Could not load this lesson.");
  }
}

watch(lessonSlug, (slug) => void load(slug), { immediate: true });

// Reaching a step is what records progress - so it's reported on arrival,
// not on leaving, and not only for the step the lesson opened at.
watch(
  () => store.currentStep?.slug,
  (slug) => {
    if (slug) void store.markSeen(slug);
  },
);

function goNext(): void {
  store.nextStep();
}

function goPrevious(): void {
  store.previousStep();
}

async function backToRoadmap(): Promise<void> {
  await router.push("/learn");
}
</script>

<template>
  <main class="min-h-screen bg-slate-50 px-4 py-10">
    <div class="mx-auto max-w-2xl">
      <p v-if="store.isLoadingLesson" class="text-sm text-slate-500">Loading lesson…</p>

      <BaseCard v-else-if="loadError">
        <p class="text-sm text-red-600" role="alert">{{ loadError }}</p>
        <div class="mt-4 flex gap-2">
          <BaseButton variant="secondary" @click="load(lessonSlug)">Try again</BaseButton>
          <BaseButton variant="ghost" @click="backToRoadmap">Back to the roadmap</BaseButton>
        </div>
      </BaseCard>

      <template v-else-if="store.lesson">
        <header class="mb-6">
          <RouterLink
            to="/learn"
            class="text-xs font-medium uppercase tracking-wide text-slate-500 hover:text-slate-900"
          >
            {{ store.lesson.course.title }}
          </RouterLink>
          <h1 class="mt-1 text-xl font-semibold text-slate-900">{{ store.lesson.title }}</h1>

          <div class="mt-4 flex items-center gap-3">
            <div class="h-1.5 flex-1 overflow-hidden rounded-full bg-slate-200">
              <div
                class="h-full rounded-full bg-slate-900 transition-all duration-300"
                :style="{ width: `${percent}%` }"
              />
            </div>
            <span class="shrink-0 text-xs font-medium tabular-nums text-slate-500">
              {{ stepNumber }} / {{ stepTotal }}
            </span>
          </div>
        </header>

        <BaseCard>
          <ReadingStep
            v-if="store.currentStep?.kind === 'reading'"
            :key="store.currentStep.id"
            :step="store.currentStep"
          />
          <MultipleChoiceStep
            v-else-if="store.currentStep?.kind === 'quiz'"
            :key="store.currentStep.id"
            :step="store.currentStep"
          />
          <CompositionStep
            v-else-if="store.currentStep?.kind === 'composition'"
            :key="store.currentStep.id"
            :step="store.currentStep"
          />
          <p v-else class="text-sm text-slate-500">This lesson has no content yet.</p>
        </BaseCard>

        <nav class="mt-6 flex items-center justify-between">
          <BaseButton variant="secondary" :disabled="store.isFirstStep" @click="goPrevious">
            Previous
          </BaseButton>
          <BaseButton v-if="!store.isLastStep" @click="goNext">Next</BaseButton>
        </nav>

        <LessonCompletion v-if="store.isLastStep" />
      </template>
    </div>
  </main>
</template>
