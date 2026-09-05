<script setup lang="ts">
/**
 * Copies the current selection, or pastes what was last copied at the
 * cursor - the toolbar's clickable equivalent of Ctrl/Cmd+C and Ctrl/Cmd+V,
 * the same on-ramp every other keyboard shortcut here gets.
 */
defineProps<{
  canCopy: boolean;
  canPaste: boolean;
}>();

const emit = defineEmits<{
  (event: "copy"): void;
  (event: "paste"): void;
}>();
</script>

<template>
  <div class="flex items-center gap-1.5">
    <button
      type="button"
      class="flex h-9 items-center gap-1.5 rounded-md border border-slate-200 bg-white px-3 text-sm font-medium text-slate-700 transition-colors hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-40"
      :disabled="!canCopy"
      title="Copy the selection (Ctrl/Cmd+C)"
      @click="emit('copy')"
    >
      <span aria-hidden="true">⧉</span>
      Copy
    </button>
    <button
      type="button"
      class="flex h-9 items-center gap-1.5 rounded-md border border-slate-200 bg-white px-3 text-sm font-medium text-slate-700 transition-colors hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-40"
      :disabled="!canPaste"
      title="Paste at the cursor (Ctrl/Cmd+V)"
      @click="emit('paste')"
    >
      <span aria-hidden="true">📋</span>
      Paste
    </button>
  </div>
</template>
