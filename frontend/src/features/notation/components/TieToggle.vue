<script setup lang="ts">
/**
 * Ties the most recently entered note to whatever follows it.
 *
 * Acts on "the note before the cursor" rather than a click-selected note -
 * see useNotationEditor's `noteBeforeCursor` - so the natural flow is: enter
 * a note, enter the note it should tie into, then press Tie. Disabled when
 * there's nothing eligible there yet (start of a voice, or the note is a
 * rest - rests don't tie).
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
    title="Tie to the next note (T)"
    @click="emit('toggle')"
  >
    <span aria-hidden="true">⌣</span>
    Tie
  </button>
</template>
