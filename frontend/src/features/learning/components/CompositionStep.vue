<script setup lang="ts">
/**
 * A composition task: the brief, the staff editor, and the graded result.
 *
 * The document lives locally, not in the store - unlike a quiz answer,
 * there's real editing state (cursor, active duration, undo-worthy content)
 * that belongs to this one open step, not to the lesson as a whole. Only
 * the *result* of a submission goes through the store, the same place a
 * quiz answer does, so it survives navigating to another step and back.
 *
 * Every attempt is free and kept forever (see the build plan's design
 * decisions) - so unlike `MultipleChoiceStep`, a submission never locks the
 * editor. The student can keep changing the score and submit again; each
 * submission just replaces the result shown below it.
 */
import { computed, ref, watch } from "vue";

import type { SkillLevel } from "@/features/feedback/types";
import { notationApi } from "@/features/notation/api";
import NotationEditor from "@/features/notation/components/NotationEditor.vue";
import { createDocument } from "@/features/notation/document";
import type { NotationDocument } from "@/features/notation/types";
import { BaseButton } from "@/shared/components/base";
import { toApiProblem } from "@/shared/utils/api-error";

import { useLearningStore } from "../stores/learning.store";
import type { CadenceKind, CompositionStep, Requirement } from "../types";

const props = defineProps<{ step: CompositionStep }>();

const store = useLearningStore();

const SKILL_LEVELS: SkillLevel[] = ["beginner", "intermediate", "advanced"];
const skillLevel = ref<SkillLevel>("intermediate");
const withAiFeedback = ref(false);
const isSubmitting = ref(false);
const submitError = ref("");

const document = ref<NotationDocument>(props.step.starterNotation ?? createDocument());
const isImporting = ref(false);
const importError = ref("");

// A different task means a different score - without this, moving between
// two composition steps would carry the previous one's notation across.
watch(
  () => props.step.slug,
  () => {
    document.value = props.step.starterNotation ?? createDocument();
    submitError.value = "";
    importError.value = "";
  },
);

/**
 * Opens an uploaded score in the editor in place of whatever's there -
 * exactly like loading a starter document, so submitting it afterwards
 * goes through the same grading pipeline as anything typed or clicked in.
 * The student can keep editing it before submitting; nothing here submits
 * on its own.
 */
async function handleFileUpload(event: Event): Promise<void> {
  const input = event.target as HTMLInputElement;
  const file = input.files?.[0];
  input.value = ""; // lets the same file be picked again after an error
  if (!file) return;

  isImporting.value = true;
  importError.value = "";
  try {
    document.value = await notationApi.importMusicXml(file);
  } catch (error) {
    importError.value = toApiProblem(error).detail ?? "Could not open that file.";
  } finally {
    isImporting.value = false;
  }
}

const result = computed(() => store.compositionResults[props.step.slug] ?? null);

function describe(requirement: Requirement): string {
  switch (requirement.type) {
    case "key":
      return `In ${requirement.key}`;
    case "time_signature":
      return `In ${requirement.value} time`;
    case "measure_count":
      return `${requirement.count} measures long`;
    case "cadence": {
      const labels: Record<CadenceKind, string> = {
        perfect_authentic: "Ends with a perfect authentic cadence",
        imperfect_authentic: "Ends with an imperfect authentic cadence",
        half: "Ends with a half cadence",
        plagal: "Ends with a plagal cadence",
        deceptive: "Ends with a deceptive cadence",
      };
      return labels[requirement.cadence];
    }
    case "range": {
      const parts: string[] = [];
      if (requirement.maxSemitones !== null) {
        parts.push(`spans no more than ${requirement.maxSemitones} semitones`);
      }
      if (requirement.lowest !== null) parts.push(`no lower than ${requirement.lowest}`);
      if (requirement.highest !== null) parts.push(`no higher than ${requirement.highest}`);
      return `Range ${parts.join(", ")}`;
    }
    case "max_leap":
      return `No leap larger than ${requirement.semitones} semitones`;
    case "leap_recovery":
      return requirement.maxUnresolved === 0
        ? "Every leap answered by a step in the opposite direction"
        : `At most ${requirement.maxUnresolved} leap(s) left unanswered`;
    case "diatonic_only":
      return "No notes outside the key";
    case "required_scale_degrees":
      return `Uses scale degree(s) ${requirement.degrees.join(", ")}`;
    case "forbidden_pitches":
      return `Avoids ${requirement.pitches.join(", ")}`;
  }
}

const requirementDescriptions = computed(() => props.step.requirements.map(describe));

async function submit(): Promise<void> {
  if (isSubmitting.value) return;
  isSubmitting.value = true;
  submitError.value = "";
  try {
    await store.submitComposition(
      props.step.slug,
      document.value,
      skillLevel.value,
      withAiFeedback.value,
    );
  } catch (error) {
    submitError.value = toApiProblem(error).detail ?? "Could not submit that composition.";
  } finally {
    isSubmitting.value = false;
  }
}
</script>

<template>
  <section>
    <p class="text-xs font-medium uppercase tracking-wide text-slate-500">Composition task</p>
    <p class="mt-2 text-[15px] leading-7 text-slate-800">{{ step.brief }}</p>

    <div v-if="requirementDescriptions.length" class="mt-5">
      <h4 class="text-sm font-semibold text-slate-900">Requirements</h4>
      <ul class="mt-2 space-y-1 text-sm text-slate-700">
        <li v-for="requirement in requirementDescriptions" :key="requirement" class="flex gap-2">
          <span class="text-slate-400">·</span>
          <span>{{ requirement }}</span>
        </li>
      </ul>
    </div>

    <div class="mt-6 flex items-center gap-2">
      <label class="text-sm text-slate-600">
        Or open a MusicXML file instead:
        <input
          type="file"
          accept=".xml,.musicxml,.mxl"
          class="ml-2 text-sm text-slate-600"
          :disabled="isImporting"
          @change="handleFileUpload"
        />
      </label>
      <span v-if="isImporting" class="text-sm text-slate-500">Opening…</span>
    </div>
    <p v-if="importError" class="mt-2 text-sm text-red-600" role="alert">{{ importError }}</p>

    <div class="mt-4">
      <NotationEditor v-model="document" :locked-staff-indices="step.lockedStaffIndices" />
    </div>

    <div class="mt-4 flex flex-wrap items-center gap-4">
      <label class="flex items-center gap-2 text-sm text-slate-700">
        Skill level
        <select
          v-model="skillLevel"
          class="rounded-md border border-slate-300 px-2 py-1 text-sm shadow-sm focus:border-slate-500 focus:outline-none focus:ring-1 focus:ring-slate-500"
        >
          <option v-for="level in SKILL_LEVELS" :key="level" :value="level">{{ level }}</option>
        </select>
      </label>
      <label class="flex items-center gap-2 text-sm text-slate-700">
        <input v-model="withAiFeedback" type="checkbox" class="h-4 w-4 accent-slate-900" />
        Get AI feedback
      </label>
      <BaseButton :disabled="isSubmitting" @click="submit">
        {{ isSubmitting ? "Submitting…" : result ? "Submit again" : "Submit" }}
      </BaseButton>
    </div>

    <p v-if="submitError" class="mt-3 text-sm text-red-600" role="alert">{{ submitError }}</p>

    <div v-if="result" class="mt-6 space-y-5" role="status">
      <p
        class="text-sm font-semibold"
        :class="result.passed ? 'text-emerald-700' : 'text-red-700'"
      >
        {{ result.passed ? "Every requirement met." : "Not quite there yet." }}
      </p>

      <ul class="space-y-1.5 text-sm">
        <li
          v-for="(item, index) in result.requirementResults"
          :key="index"
          class="flex items-start gap-2"
        >
          <span :class="item.passed ? 'text-emerald-600' : 'text-red-600'">
            {{ item.passed ? "✓" : "✗" }}
          </span>
          <span :class="item.passed ? 'text-slate-700' : 'text-slate-900'">
            {{ item.message }}
            <span v-if="item.measure !== null" class="text-slate-400">(m. {{ item.measure }})</span>
          </span>
        </li>
      </ul>

      <div v-if="withAiFeedback && !result.aiFeedback" class="text-sm text-slate-500">
        AI feedback isn't available for this submission - deterministic grading above is unaffected.
      </div>

      <div v-if="result.aiFeedback" class="space-y-4 rounded-md border border-slate-200 bg-slate-50 p-4">
        <p class="text-sm text-slate-700">{{ result.aiFeedback.summary }}</p>

        <section v-if="result.aiFeedback.strengths.length">
          <h4 class="text-xs font-semibold uppercase tracking-wide text-slate-500">Strengths</h4>
          <ul class="mt-1.5 list-inside list-disc space-y-1 text-sm text-slate-700">
            <li v-for="(strength, index) in result.aiFeedback.strengths" :key="index">
              {{ strength }}
            </li>
          </ul>
        </section>

        <section v-if="result.aiFeedback.issues.length" class="space-y-3">
          <h4 class="text-xs font-semibold uppercase tracking-wide text-slate-500">To work on</h4>
          <div
            v-for="(issue, index) in result.aiFeedback.issues"
            :key="index"
            class="space-y-2 rounded-md border border-slate-200 bg-white p-3"
          >
            <p class="text-sm font-medium text-slate-900">{{ issue.problem }}</p>
            <p class="text-sm text-slate-600">{{ issue.explanation }}</p>
            <p class="text-sm text-slate-600"><strong>Try:</strong> {{ issue.suggestion }}</p>
            <p class="text-xs text-slate-500">
              <strong>{{ issue.theory.concept }}:</strong> {{ issue.theory.lesson }}
            </p>
          </div>
        </section>

        <section v-if="result.aiFeedback.suggestions.length">
          <h4 class="text-xs font-semibold uppercase tracking-wide text-slate-500">Next steps</h4>
          <ul class="mt-1.5 list-inside list-disc space-y-1 text-sm text-slate-700">
            <li v-for="(suggestion, index) in result.aiFeedback.suggestions" :key="index">
              {{ suggestion }}
            </li>
          </ul>
        </section>
      </div>
    </div>
  </section>
</template>
