<script setup lang="ts">
/**
 * Adds or removes a measure from the end of the score.
 *
 * Disabled rather than hidden at either bound: a composition task that
 * names a bar count ("an 8-bar melody") passes `min`/`max` down from
 * `useNotationEditor`'s options, and a control the student can see but not
 * push past is a clearer signal than one that vanishes.
 */
defineProps<{
  count: number;
  canAdd: boolean;
  canRemove: boolean;
}>();

const emit = defineEmits<{
  (event: "add"): void;
  (event: "remove"): void;
}>();
</script>

<template>
  <div class="flex items-center gap-2" role="group" aria-label="Measures">
    <button
      type="button"
      class="flex h-9 w-9 items-center justify-center rounded-md border border-slate-200 bg-white text-lg font-medium text-slate-700 transition-colors hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-40"
      :disabled="!canRemove"
      title="Remove the last measure"
      @click="emit('remove')"
    >
      −
    </button>
    <span class="min-w-[6rem] text-center text-sm text-slate-600">
      {{ count }} {{ count === 1 ? "measure" : "measures" }}
    </span>
    <button
      type="button"
      class="flex h-9 w-9 items-center justify-center rounded-md border border-slate-200 bg-white text-lg font-medium text-slate-700 transition-colors hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-40"
      :disabled="!canAdd"
      title="Add a measure"
      @click="emit('add')"
    >
      +
    </button>
  </div>
</template>
