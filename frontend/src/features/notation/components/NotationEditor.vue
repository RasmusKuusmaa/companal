<script setup lang="ts">
/**
 * The staff editor.
 *
 * Composes the renderer with the editing state and whatever controls have
 * been built so far. The document is owned here and exposed through
 * `v-model`, so the page around it - a lesson step, an exam question -
 * holds the score without knowing anything about how it's edited.
 */
import { watch } from "vue";

import { useNotationEditor } from "../composables/useNotationEditor";
import type { NotationDocument } from "../types";
import DurationPalette from "./DurationPalette.vue";
import StaffRenderer from "./StaffRenderer.vue";

const props = defineProps<{
  modelValue: NotationDocument;
}>();

const emit = defineEmits<{
  (event: "update:modelValue", value: NotationDocument): void;
}>();

const editor = useNotationEditor(props.modelValue);

// The document flows both ways: the parent may replace it (loading a
// starter score, resetting an exercise), and every edit flows back out.
watch(
  () => props.modelValue,
  (next) => {
    if (next !== editor.document.value) editor.setDocument(next);
  },
);

watch(editor.document, (next) => emit("update:modelValue", next));
</script>

<template>
  <div class="flex flex-col gap-3">
    <DurationPalette
      :duration="editor.activeDuration.value"
      :dots="editor.activeDots.value"
      @update:duration="editor.setDuration"
      @update:dots="editor.setDots"
    />

    <StaffRenderer :document="editor.document.value" @staff-click="editor.placeAt" />

    <p v-if="editor.lastRefusal.value" class="text-sm text-amber-700" role="status">
      {{ editor.lastRefusal.value }}
    </p>
  </div>
</template>
