<script setup lang="ts">
/**
 * Forces (or lifts) a beam break just after the most recently entered note.
 *
 * Acts on "the note before the cursor", the same target the tie control
 * uses - enter a run of eighths, then press Break Beam right after the one
 * where the beam should split. Disabled when there's nothing eligible
 * there yet (start of a voice, a rest, or a note too long to beam at all).
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
    title="Break the beam here (K)"
    @click="emit('toggle')"
  >
    <span aria-hidden="true">⌐</span>
    Break Beam
  </button>
</template>
