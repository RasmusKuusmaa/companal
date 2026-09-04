<script setup lang="ts">
/**
 * A composition task: the brief, and what the submission has to satisfy.
 *
 * The staff editor and submission flow arrive in Phase F; until then this
 * shows the task honestly rather than pretending to accept work it can't
 * yet grade. Each requirement is rendered as the plain-English sentence a
 * student would actually want to read - the same requirement objects the
 * backend's validators check against (see `notation.requirements` and
 * `notation.validation` on the backend for where these are enforced).
 */
import { computed } from "vue";

import type { CadenceKind, CompositionStep, Requirement } from "../types";

const props = defineProps<{ step: CompositionStep }>();

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

const requirements = computed(() => props.step.requirements.map(describe));
</script>

<template>
  <section>
    <p class="text-xs font-medium uppercase tracking-wide text-slate-500">Composition task</p>
    <p class="mt-2 text-[15px] leading-7 text-slate-800">{{ step.brief }}</p>

    <div v-if="requirements.length" class="mt-5">
      <h4 class="text-sm font-semibold text-slate-900">Requirements</h4>
      <ul class="mt-2 space-y-1 text-sm text-slate-700">
        <li v-for="requirement in requirements" :key="requirement" class="flex gap-2">
          <span class="text-slate-400">·</span>
          <span>{{ requirement }}</span>
        </li>
      </ul>
    </div>

    <p
      class="mt-6 rounded-md border border-dashed border-slate-300 bg-slate-50 p-4 text-sm text-slate-600"
    >
      The staff editor for writing and submitting this task is not built yet.
    </p>
  </section>
</template>
