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
import AccidentalPalette from "./AccidentalPalette.vue";
import DurationPalette from "./DurationPalette.vue";
import RestToggle from "./RestToggle.vue";
import StaffRenderer, { type StaffClick } from "./StaffRenderer.vue";
import TieToggle from "./TieToggle.vue";

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

/**
 * A click either selects an existing note or places a new one - never both.
 * Clicking a note head means "put the cursor here", the same as clicking a
 * word in a text editor; it would be surprising if it also inserted a
 * duplicate note under the pointer.
 */
function handleStaffClick(click: StaffClick): void {
  if (click.noteId) {
    editor.selectNote(click.noteId);
  } else {
    editor.placeAt(click);
  }
}

/**
 * Arrow keys move the cursor, Backspace/Delete remove around it - the same
 * bindings a text editor uses, which is deliberate: anyone who has typed
 * text already knows this vocabulary, and it's one less thing to teach
 * before a student can start writing music.
 *
 * Scoped to this component's own keydown (via the wrapping div's tabindex),
 * not a window listener - so the editor only responds to these keys when
 * it actually has focus, and never fights the browser's own shortcuts
 * elsewhere on the page.
 */
function handleKeydown(event: KeyboardEvent): void {
  switch (event.key) {
    case "ArrowLeft":
      event.preventDefault();
      editor.moveLeft();
      break;
    case "ArrowRight":
      event.preventDefault();
      editor.moveRight();
      break;
    case "Backspace":
      event.preventDefault();
      editor.deleteBefore();
      break;
    case "Delete":
      event.preventDefault();
      editor.deleteAtCursor();
      break;
  }
}
</script>

<template>
  <div class="flex flex-col gap-3" tabindex="0" @keydown="handleKeydown">
    <div class="flex flex-wrap items-center gap-4">
      <DurationPalette
        :duration="editor.activeDuration.value"
        :dots="editor.activeDots.value"
        @update:duration="editor.setDuration"
        @update:dots="editor.setDots"
      />
      <AccidentalPalette :alter="editor.activeAlter.value" @update:alter="editor.setAlter" />
      <RestToggle :active="editor.activeIsRest.value" @update:active="editor.setRestMode" />
      <TieToggle
        :active="editor.isTiedAtCursor.value"
        :disabled="!editor.canTieAtCursor.value"
        @toggle="editor.toggleTie"
      />
    </div>

    <StaffRenderer
      :document="editor.document.value"
      :cursor-note-id="editor.cursorNoteId.value"
      @staff-click="handleStaffClick"
    />

    <p v-if="editor.lastRefusal.value" class="text-sm text-amber-700" role="status">
      {{ editor.lastRefusal.value }}
    </p>
  </div>
</template>
