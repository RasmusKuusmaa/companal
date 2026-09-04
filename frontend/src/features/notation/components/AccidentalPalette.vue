<script setup lang="ts">
/**
 * Picks the accidental the next placed note carries.
 *
 * Unlike duration, this resets after every note - see useNotationEditor.
 * Selecting sharp and clicking twice should produce one sharp note and one
 * plain one, matching every notation program's convention, not two sharps.
 */
import { ACCIDENTALS } from "../constants";

const props = defineProps<{
  alter: number;
}>();

const emit = defineEmits<{
  (event: "update:alter", value: number): void;
}>();

function toggle(alter: number): void {
  // Clicking the already-active accidental clears it, the same way
  // toggling any other modal control does.
  emit("update:alter", props.alter === alter ? 0 : alter);
}
</script>

<template>
  <div class="flex flex-wrap items-center gap-1" role="group" aria-label="Accidental">
    <button
      v-for="spec in ACCIDENTALS"
      :key="spec.alter"
      type="button"
      class="flex h-9 w-9 items-center justify-center rounded-md border text-base font-medium transition-colors"
      :class="
        alter === spec.alter
          ? 'border-slate-900 bg-slate-900 text-white'
          : 'border-slate-200 bg-white text-slate-700 hover:bg-slate-50'
      "
      :aria-pressed="alter === spec.alter"
      :title="spec.label"
      @click="toggle(spec.alter)"
    >
      {{ spec.symbol }}
    </button>
  </div>
</template>
