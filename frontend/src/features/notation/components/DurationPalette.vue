<script setup lang="ts">
/**
 * Picks the duration and dot count the next placed note will use.
 *
 * This is modal state, not per-click state - see useNotationEditor for why:
 * writing a run of eighths should be a run of clicks, not a duration picked
 * before each one. The toolbar just exposes what's already there to edit.
 */
import { DURATIONS, MAX_DOTS } from "../constants";
import type { DurationName } from "../types";

const props = defineProps<{
  duration: DurationName;
  dots: number;
}>();

const emit = defineEmits<{
  (event: "update:duration", value: DurationName): void;
  (event: "update:dots", value: number): void;
}>();

function toggleDots(): void {
  const next = props.dots >= MAX_DOTS ? 0 : props.dots + 1;
  emit("update:dots", next);
}
</script>

<template>
  <div class="flex flex-wrap items-center gap-1" role="group" aria-label="Note duration">
    <button
      v-for="spec in DURATIONS"
      :key="spec.name"
      type="button"
      class="flex h-9 min-w-9 items-center justify-center rounded-md border px-2 text-sm font-medium transition-colors"
      :class="
        duration === spec.name
          ? 'border-slate-900 bg-slate-900 text-white'
          : 'border-slate-200 bg-white text-slate-700 hover:bg-slate-50'
      "
      :aria-pressed="duration === spec.name"
      :title="`${spec.label} (${spec.shortcut})`"
      @click="emit('update:duration', spec.name)"
    >
      {{ spec.label }}
    </button>

    <button
      type="button"
      class="flex h-9 min-w-9 items-center justify-center rounded-md border px-2 text-sm font-medium transition-colors"
      :class="
        dots > 0
          ? 'border-slate-900 bg-slate-900 text-white'
          : 'border-slate-200 bg-white text-slate-700 hover:bg-slate-50'
      "
      :aria-pressed="dots > 0"
      title="Augmentation dot (.)"
      @click="toggleDots"
    >
      {{ ".".repeat(Math.max(dots, 1)) }}
    </button>
  </div>
</template>
