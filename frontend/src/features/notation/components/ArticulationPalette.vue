<script setup lang="ts">
/**
 * Sets (or, clicking the active one again, clears) an articulation mark on
 * the most recently entered note - same target as the tie and slur
 * controls, and the same reason: marking a note that's already on the page
 * is the natural flow, not choosing a mark before writing the note.
 */
import type { ArticulationKind } from "../types";

defineProps<{
  active: ArticulationKind | null;
  disabled: boolean;
}>();

const emit = defineEmits<{
  (event: "select", kind: ArticulationKind): void;
}>();

const MARKS: { kind: ArticulationKind; label: string; glyph: string; shortcut: string }[] = [
  { kind: "staccato", label: "Staccato", glyph: "·", shortcut: "U" },
  { kind: "accent", label: "Accent", glyph: ">", shortcut: "V" },
  { kind: "tenuto", label: "Tenuto", glyph: "−", shortcut: "N" },
  { kind: "marcato", label: "Marcato", glyph: "^", shortcut: "M" },
];
</script>

<template>
  <div class="flex items-center gap-1.5">
    <button
      v-for="mark in MARKS"
      :key="mark.kind"
      type="button"
      class="flex h-9 w-9 items-center justify-center rounded-md border text-sm font-medium transition-colors disabled:cursor-not-allowed disabled:opacity-40"
      :class="
        active === mark.kind
          ? 'border-slate-900 bg-slate-900 text-white'
          : 'border-slate-200 bg-white text-slate-700 hover:bg-slate-50'
      "
      :aria-pressed="active === mark.kind"
      :disabled="disabled"
      :title="`${mark.label} (${mark.shortcut})`"
      @click="emit('select', mark.kind)"
    >
      <span aria-hidden="true">{{ mark.glyph }}</span>
      <span class="sr-only">{{ mark.label }}</span>
    </button>
  </div>
</template>
