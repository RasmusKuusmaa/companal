<script setup lang="ts">
/**
 * A ring showing "how much of this is done", with the fraction in the
 * middle.
 *
 * Drawn with a stroked circle and `stroke-dasharray` rather than an arc
 * path: the geometry stays a single number (how much of the circumference
 * to paint), so there's no arc-flag maths to get wrong at the 50% mark.
 */
import { computed } from "vue";

const props = withDefaults(
  defineProps<{
    completed: number;
    total: number;
    size?: number;
  }>(),
  { size: 44 },
);

const RADIUS = 20;
const CIRCUMFERENCE = 2 * Math.PI * RADIUS;

const fraction = computed(() => (props.total > 0 ? props.completed / props.total : 0));
const dash = computed(() => `${fraction.value * CIRCUMFERENCE} ${CIRCUMFERENCE}`);
const isComplete = computed(() => props.total > 0 && props.completed === props.total);
</script>

<template>
  <div
    class="relative shrink-0"
    :style="{ width: `${size}px`, height: `${size}px` }"
    role="img"
    :aria-label="`${completed} of ${total} lessons complete`"
  >
    <svg viewBox="0 0 48 48" class="h-full w-full -rotate-90">
      <circle
        cx="24"
        cy="24"
        :r="RADIUS"
        fill="none"
        stroke="currentColor"
        stroke-width="4"
        class="text-slate-200"
      />
      <circle
        cx="24"
        cy="24"
        :r="RADIUS"
        fill="none"
        stroke="currentColor"
        stroke-width="4"
        stroke-linecap="round"
        :stroke-dasharray="dash"
        class="transition-all duration-300"
        :class="isComplete ? 'text-emerald-600' : 'text-slate-900'"
      />
    </svg>
    <span
      class="absolute inset-0 flex items-center justify-center text-[11px] font-semibold tabular-nums"
      :class="isComplete ? 'text-emerald-700' : 'text-slate-700'"
    >
      {{ completed }}/{{ total }}
    </span>
  </div>
</template>
