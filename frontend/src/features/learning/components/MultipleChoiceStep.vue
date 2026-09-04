<script setup lang="ts">
/**
 * A multiple-choice check.
 *
 * Grading happens on the server - the step this component receives has no
 * answer key in it, so there is nothing here to cheat against. The result
 * comes back from the submission and is held in the store per step slug, so
 * navigating away and back shows the same verdict rather than a blank
 * question.
 */
import { computed, ref, watch } from "vue";

import { BaseButton } from "@/shared/components/base";
import { toApiProblem } from "@/shared/utils/api-error";

import { useLearningStore } from "../stores/learning.store";
import type { QuizStep } from "../types";

const props = defineProps<{ step: QuizStep }>();

const store = useLearningStore();
const selected = ref<number | null>(null);
const isSubmitting = ref(false);
const submitError = ref("");

const result = computed(() => store.quizResults[props.step.slug] ?? null);
const isAnswered = computed(() => result.value !== null);

// A different question means a different selection; without this, moving
// between two quiz steps would carry the previous choice across.
watch(
  () => props.step.slug,
  () => {
    selected.value = null;
    submitError.value = "";
  },
);

async function submit(): Promise<void> {
  if (selected.value === null || isSubmitting.value) return;
  isSubmitting.value = true;
  submitError.value = "";
  try {
    await store.answerQuiz(props.step.slug, selected.value);
  } catch (error) {
    submitError.value = toApiProblem(error).detail ?? "Could not submit that answer.";
  } finally {
    isSubmitting.value = false;
  }
}
</script>

<template>
  <section>
    <h3 class="text-base font-semibold text-slate-900">{{ step.question }}</h3>

    <fieldset class="mt-4 space-y-2" :disabled="isAnswered">
      <legend class="sr-only">{{ step.question }}</legend>
      <label
        v-for="(choice, index) in step.choices"
        :key="index"
        class="flex cursor-pointer items-start gap-3 rounded-md border p-3 text-sm transition-colors"
        :class="
          selected === index ? 'border-slate-900 bg-slate-50' : 'border-slate-200 hover:bg-slate-50'
        "
      >
        <input
          v-model="selected"
          type="radio"
          :value="index"
          :name="`quiz-${step.slug}`"
          class="mt-0.5 h-4 w-4 accent-slate-900"
        />
        <span class="text-slate-700">{{ choice }}</span>
      </label>
    </fieldset>

    <p v-if="submitError" class="mt-3 text-sm text-red-600" role="alert">{{ submitError }}</p>

    <div v-if="!isAnswered" class="mt-4">
      <BaseButton :disabled="selected === null || isSubmitting" @click="submit">
        {{ isSubmitting ? "Checking…" : "Check answer" }}
      </BaseButton>
    </div>

    <p
      v-else
      class="mt-4 text-sm font-semibold"
      :class="result?.isCorrect ? 'text-emerald-700' : 'text-red-700'"
      role="status"
    >
      {{ result?.isCorrect ? "Correct." : "Not quite." }}
    </p>
  </section>
</template>
