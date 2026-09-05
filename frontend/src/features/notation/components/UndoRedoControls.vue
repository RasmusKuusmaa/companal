<script setup lang="ts">
/**
 * Steps back through (or re-applies) the editor's edit history - the
 * toolbar's clickable equivalent of Ctrl/Cmd+Z and Ctrl/Cmd+Shift+Z.
 */
defineProps<{
  canUndo: boolean;
  canRedo: boolean;
}>();

const emit = defineEmits<{
  (event: "undo"): void;
  (event: "redo"): void;
}>();
</script>

<template>
  <div class="flex items-center gap-1.5">
    <button
      type="button"
      class="flex h-9 items-center gap-1.5 rounded-md border border-slate-200 bg-white px-3 text-sm font-medium text-slate-700 transition-colors hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-40"
      :disabled="!canUndo"
      title="Undo (Ctrl/Cmd+Z)"
      @click="emit('undo')"
    >
      <span aria-hidden="true">↶</span>
      Undo
    </button>
    <button
      type="button"
      class="flex h-9 items-center gap-1.5 rounded-md border border-slate-200 bg-white px-3 text-sm font-medium text-slate-700 transition-colors hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-40"
      :disabled="!canRedo"
      title="Redo (Ctrl/Cmd+Shift+Z)"
      @click="emit('redo')"
    >
      <span aria-hidden="true">↷</span>
      Redo
    </button>
  </div>
</template>
