<script setup lang="ts">
/**
 * Switches the editor between entering pitched notes and entering rests.
 *
 * A rest is entered through the same staff click as a note - see
 * `useNotationEditor` - so this is the one control that changes what a
 * click means rather than a property of the note it produces.
 */
defineProps<{
  active: boolean;
}>();

const emit = defineEmits<{
  (event: "update:active", value: boolean): void;
}>();
</script>

<template>
  <button
    type="button"
    class="flex h-9 items-center gap-1.5 rounded-md border px-3 text-sm font-medium transition-colors"
    :class="
      active
        ? 'border-slate-900 bg-slate-900 text-white'
        : 'border-slate-200 bg-white text-slate-700 hover:bg-slate-50'
    "
    :aria-pressed="active"
    title="Rest (R)"
    @click="emit('update:active', !active)"
  >
    <span aria-hidden="true">𝄽</span>
    Rest
  </button>
</template>
