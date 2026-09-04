<script setup lang="ts">
/**
 * A composition task: the brief, and what the submission has to satisfy.
 *
 * The staff editor and the grading pipeline arrive in later phases; until
 * then this shows the task honestly rather than pretending to accept work
 * it can't yet mark. The requirements are rendered from the raw rule object
 * because the rule language doesn't have a schema yet either - once it
 * does, this becomes a proper checklist rather than key/value pairs.
 */
import { computed } from "vue";

import type { CompositionStep } from "../types";

const props = defineProps<{ step: CompositionStep }>();

const requirements = computed(() => Object.entries(props.step.requirements));
</script>

<template>
  <section>
    <p class="text-xs font-medium uppercase tracking-wide text-slate-500">Composition task</p>
    <p class="mt-2 text-[15px] leading-7 text-slate-800">{{ step.brief }}</p>

    <div v-if="requirements.length" class="mt-5">
      <h4 class="text-sm font-semibold text-slate-900">Requirements</h4>
      <ul class="mt-2 space-y-1 text-sm text-slate-700">
        <li v-for="[name, value] in requirements" :key="name" class="flex gap-2">
          <span class="text-slate-400">·</span>
          <span>
            <span class="font-medium">{{ name.replace(/_/g, " ") }}</span>
            <span class="text-slate-500"> — {{ value }}</span>
          </span>
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
