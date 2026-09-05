<script setup lang="ts">
/**
 * Slurs the most recently entered note into whatever follows it - a
 * phrasing mark, not a same-pitch requirement the way a tie is.
 *
 * Acts on "the note before the cursor", the same target the tie and
 * break-beam controls use. Disabled when there's nothing eligible there
 * yet (start of a voice, or the note is a rest).
 */
defineProps<{
  active: boolean;
  disabled: boolean;
}>();

const emit = defineEmits<{
  (event: "toggle"): void;
}>();
</script>

<template>
  <button
    type="button"
    class="flex h-9 items-center gap-1.5 rounded-md border px-3 text-sm font-medium transition-colors disabled:cursor-not-allowed disabled:opacity-40"
    :class="
      active
        ? 'border-slate-900 bg-slate-900 text-white'
        : 'border-slate-200 bg-white text-slate-700 hover:bg-slate-50'
    "
    :aria-pressed="active"
    :disabled="disabled"
    title="Slur to the next note (S)"
    @click="emit('toggle')"
  >
    <span aria-hidden="true">⌣</span>
    Slur
  </button>
</template>
