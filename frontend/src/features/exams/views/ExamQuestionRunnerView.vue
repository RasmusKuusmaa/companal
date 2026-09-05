<script setup lang="ts">
/**
 * Answers a fresh exam attempt, sectioned by question kind.
 *
 * Nothing is revealed while answering - no correct/incorrect marker on a
 * quiz choice, no pass/fail on a composition - because nothing is graded
 * until the whole attempt is submitted (see the backend's `ExamAttempt`).
 * That's the one deliberate difference from a lesson's quiz and
 * composition steps, which grade and reveal immediately.
 */
import { computed, onMounted, reactive, ref } from "vue";
import { useRoute, useRouter } from "vue-router";

import type { SkillLevel } from "@/features/feedback/types";
import { createDocument } from "@/features/notation/document";
import NotationEditor from "@/features/notation/components/NotationEditor.vue";
import type { NotationDocument } from "@/features/notation/types";
import { BaseButton, BaseCard } from "@/shared/components/base";
import { toApiProblem } from "@/shared/utils/api-error";

import { useExamsStore } from "../stores/exams.store";
import type { ExamCompositionQuestion, ExamQuizQuestion } from "../types";

const route = useRoute();
const router = useRouter();
const store = useExamsStore();

const examSlug = computed(() => route.params.examSlug as string);
const loadError = ref("");
const submitError = ref("");

const skillLevel = ref<SkillLevel>("intermediate");
const withAiFeedback = ref(false);

const selectedChoice = reactive<Record<string, number>>({});
const documents = reactive<Record<string, NotationDocument>>({});
const savedQuestionIds = reactive<Record<string, boolean>>({});
const savingQuestionIds = reactive<Record<string, boolean>>({});

const exam = computed(() => store.currentAttempt?.exam ?? null);
const quizQuestions = computed<ExamQuizQuestion[]>(
  () => (exam.value?.questions.filter((q) => q.kind === "quiz") as ExamQuizQuestion[]) ?? [],
);
const compositionQuestions = computed<ExamCompositionQuestion[]>(
  () =>
    (exam.value?.questions.filter((q) => q.kind === "composition") as ExamCompositionQuestion[]) ??
    [],
);

const answeredCount = computed(() => Object.values(savedQuestionIds).filter(Boolean).length);
const totalCount = computed(() => exam.value?.questions.length ?? 0);

async function selectQuizChoice(question: ExamQuizQuestion, choiceIndex: number): Promise<void> {
  selectedChoice[question.id] = choiceIndex;
  savingQuestionIds[question.id] = true;
  try {
    await store.holdAnswer(question.id, { kind: "quiz", choiceIndex });
    savedQuestionIds[question.id] = true;
  } catch (error) {
    submitError.value = toApiProblem(error).detail ?? "Could not save that answer.";
  } finally {
    savingQuestionIds[question.id] = false;
  }
}

async function saveCompositionAnswer(question: ExamCompositionQuestion): Promise<void> {
  savingQuestionIds[question.id] = true;
  try {
    await store.holdAnswer(question.id, {
      kind: "composition",
      // Every composition question gets a document in `documents` during
      // `onMounted`, before this can be called.
      document: documents[question.id]!,
    });
    savedQuestionIds[question.id] = true;
  } catch (error) {
    submitError.value = toApiProblem(error).detail ?? "Could not save that answer.";
  } finally {
    savingQuestionIds[question.id] = false;
  }
}

async function submitExam(): Promise<void> {
  submitError.value = "";
  try {
    await store.submitAttempt(withAiFeedback.value, skillLevel.value);
    await router.push(`/exams/${examSlug.value}/result`);
  } catch (error) {
    submitError.value = toApiProblem(error).detail ?? "Could not submit the exam.";
  }
}

onMounted(async () => {
  try {
    const attempt = await store.startAttempt(examSlug.value);
    for (const question of attempt.exam.questions) {
      if (question.kind === "composition") {
        documents[question.id] = question.starterNotation ?? createDocument();
      }
    }
  } catch (error) {
    loadError.value = toApiProblem(error).detail ?? "Could not start this exam.";
  }
});
</script>

<template>
  <main class="min-h-screen bg-slate-50 px-4 py-10">
    <div class="mx-auto max-w-3xl">
      <p v-if="store.isStartingAttempt" class="text-sm text-slate-500">Starting the exam…</p>

      <BaseCard v-else-if="loadError">
        <p class="text-sm text-red-600" role="alert">{{ loadError }}</p>
      </BaseCard>

      <template v-else-if="exam">
        <header class="mb-8">
          <h1 class="text-xl font-semibold text-slate-900">{{ exam.title }}</h1>
          <p class="mt-1 text-sm text-slate-500">
            Attempt {{ store.currentAttempt?.attemptNumber }} · {{ answeredCount }} of
            {{ totalCount }} answered
          </p>
        </header>

        <section v-if="quizQuestions.length" class="mb-8">
          <h2 class="mb-3 text-sm font-semibold uppercase tracking-wide text-slate-500">
            Multiple choice
          </h2>
          <div class="space-y-4">
            <BaseCard v-for="question in quizQuestions" :key="question.id">
              <h3 class="text-base font-semibold text-slate-900">{{ question.question }}</h3>
              <fieldset class="mt-4 space-y-2">
                <legend class="sr-only">{{ question.question }}</legend>
                <label
                  v-for="(choice, index) in question.choices"
                  :key="index"
                  class="flex cursor-pointer items-start gap-3 rounded-md border p-3 text-sm transition-colors hover:bg-slate-50"
                  :class="
                    selectedChoice[question.id] === index
                      ? 'border-slate-900 bg-slate-50'
                      : 'border-slate-200'
                  "
                >
                  <input
                    type="radio"
                    :name="`exam-quiz-${question.id}`"
                    :checked="selectedChoice[question.id] === index"
                    class="mt-0.5 h-4 w-4 accent-slate-900"
                    @change="selectQuizChoice(question, index)"
                  />
                  <span class="flex-1 text-slate-700">{{ choice }}</span>
                </label>
              </fieldset>
              <p v-if="savedQuestionIds[question.id]" class="mt-2 text-xs text-slate-500">
                Answer saved.
              </p>
            </BaseCard>
          </div>
        </section>

        <section v-if="compositionQuestions.length" class="mb-8">
          <h2 class="mb-3 text-sm font-semibold uppercase tracking-wide text-slate-500">
            Composition
          </h2>
          <div class="space-y-4">
            <BaseCard v-for="question in compositionQuestions" :key="question.id">
              <p class="text-[15px] leading-7 text-slate-800">{{ question.brief }}</p>
              <div class="mt-4">
                <NotationEditor
                  v-if="documents[question.id]"
                  v-model="documents[question.id]!"
                  :locked-staff-indices="question.lockedStaffIndices"
                />
              </div>
              <div class="mt-4 flex items-center gap-3">
                <BaseButton
                  variant="ghost"
                  :disabled="savingQuestionIds[question.id]"
                  @click="saveCompositionAnswer(question)"
                >
                  {{ savingQuestionIds[question.id] ? "Saving…" : "Save answer" }}
                </BaseButton>
                <span v-if="savedQuestionIds[question.id]" class="text-xs text-slate-500">
                  Answer saved.
                </span>
              </div>
            </BaseCard>
          </div>
        </section>

        <BaseCard>
          <div class="flex flex-wrap items-center gap-4">
            <label class="flex items-center gap-2 text-sm text-slate-700">
              Skill level
              <select
                v-model="skillLevel"
                class="rounded-md border border-slate-300 px-2 py-1 text-sm shadow-sm focus:border-slate-500 focus:outline-none focus:ring-1 focus:ring-slate-500"
              >
                <option value="beginner">beginner</option>
                <option value="intermediate">intermediate</option>
                <option value="advanced">advanced</option>
              </select>
            </label>
            <label class="flex items-center gap-2 text-sm text-slate-700">
              <input v-model="withAiFeedback" type="checkbox" class="h-4 w-4 accent-slate-900" />
              Get AI feedback (premium)
            </label>
            <BaseButton :disabled="store.isSubmittingAttempt" @click="submitExam">
              {{ store.isSubmittingAttempt ? "Submitting…" : "Submit exam" }}
            </BaseButton>
          </div>
          <p v-if="submitError" class="mt-3 text-sm text-red-600" role="alert">{{ submitError }}</p>
        </BaseCard>
      </template>
    </div>
  </main>
</template>
