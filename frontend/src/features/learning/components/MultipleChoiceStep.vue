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

/**
 * How each choice should read once the question has been answered.
 *
 * The correct choice is always revealed, including after a wrong answer.
 * Retries are unlimited and unscored, so hiding it would only turn the
 * question into a guessing game - and the student who got it wrong is
 * precisely the one who needs to see which one was right, next to the
 * explanation of why.
 */
function choiceState(index: number): "correct" | "wrong" | "neutral" {
  const answered = result.value;
  if (!answered) return "neutral";
  if (index === answered.correctIndex) return "correct";
  if (index === selected.value) return "wrong";
  return "neutral";
}

function tryAgain(): void {
  store.retryQuiz(props.step.slug);
  selected.value = null;
}

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
        class="flex items-start gap-3 rounded-md border p-3 text-sm transition-colors"
        :class="[
          isAnswered ? 'cursor-default' : 'cursor-pointer hover:bg-slate-50',
          {
            'border-emerald-500 bg-emerald-50': choiceState(index) === 'correct',
            'border-red-400 bg-red-50': choiceState(index) === 'wrong',
            'border-slate-900 bg-slate-50':
              !isAnswered && selected === index && choiceState(index) === 'neutral',
            'border-slate-200':
              choiceState(index) === 'neutral' && !(!isAnswered && selected === index),
          },
        ]"
      >
        <input
          v-model="selected"
          type="radio"
          :value="index"
          :name="`quiz-${step.slug}`"
          class="mt-0.5 h-4 w-4 accent-slate-900"
        />
        <span class="flex-1 text-slate-700">{{ choice }}</span>
        <span
          v-if="choiceState(index) === 'correct'"
          class="text-xs font-semibold text-emerald-700"
        >
          correct
        </span>
      </label>
    </fieldset>

    <p v-if="submitError" class="mt-3 text-sm text-red-600" role="alert">{{ submitError }}</p>

    <div v-if="!isAnswered" class="mt-4">
      <BaseButton :disabled="selected === null || isSubmitting" @click="submit">
        {{ isSubmitting ? "Checking…" : "Check answer" }}
      </BaseButton>
    </div>

    <div v-else class="mt-5" role="status">
      <p
        class="text-sm font-semibold"
        :class="result?.isCorrect ? 'text-emerald-700' : 'text-red-700'"
      >
        {{ result?.isCorrect ? "Correct." : "Not quite." }}
      </p>

      <div class="mt-3 rounded-md border border-slate-200 bg-slate-50 p-4">
        <h4 class="text-xs font-semibold uppercase tracking-wide text-slate-500">Why</h4>
        <p class="mt-1.5 text-sm leading-6 text-slate-700">{{ result?.explanation }}</p>
      </div>

      <div class="mt-3">
        <BaseButton variant="ghost" @click="tryAgain">Try again</BaseButton>
      </div>
    </div>
  </section>
</template>
