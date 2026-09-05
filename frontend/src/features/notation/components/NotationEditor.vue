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
import { useNotationPlayback } from "../composables/useNotationPlayback";
import { DURATIONS, MAX_DOTS, PITCH_STEPS } from "../constants";
import type { ArticulationKind, NotationDocument, PitchStep } from "../types";
import AccidentalPalette from "./AccidentalPalette.vue";
import ArticulationPalette from "./ArticulationPalette.vue";
import BeamToggle from "./BeamToggle.vue";
import CopyPasteControls from "./CopyPasteControls.vue";
import DurationPalette from "./DurationPalette.vue";
import ExportControls from "./ExportControls.vue";
import MeasureControls from "./MeasureControls.vue";
import PlaybackTransport from "./PlaybackTransport.vue";
import RestToggle from "./RestToggle.vue";
import SlurToggle from "./SlurToggle.vue";
import StaffRenderer, { type StaffClick } from "./StaffRenderer.vue";
import StaffSelector from "./StaffSelector.vue";
import TieToggle from "./TieToggle.vue";
import UndoRedoControls from "./UndoRedoControls.vue";
import VoiceSelector from "./VoiceSelector.vue";

const ARTICULATION_SHORTCUT: Record<string, ArticulationKind> = {
  U: "staccato",
  V: "accent",
  N: "tenuto",
  M: "marcato",
};

const props = defineProps<{
  modelValue: NotationDocument;
  /** Bounds passed straight to useNotationEditor - see its own docs. */
  minMeasures?: number;
  maxMeasures?: number;
  /** Staff indices holding given material the student can't edit away. */
  lockedStaffIndices?: number[];
}>();

const emit = defineEmits<{
  (event: "update:modelValue", value: NotationDocument): void;
}>();

const editor = useNotationEditor(props.modelValue, {
  minMeasures: props.minMeasures,
  maxMeasures: props.maxMeasures,
  lockedStaffIndices: props.lockedStaffIndices,
});
const playback = useNotationPlayback(editor.document);

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
    if (click.shiftKey) editor.extendSelectionToNote(click.noteId);
    else editor.selectNote(click.noteId);
  } else {
    editor.placeAt(click);
  }
}

/**
 * Arrow keys move the cursor, Backspace/Delete remove around it, digits pick
 * a duration, "." cycles the dot, R and T toggle rest and tie mode - the
 * whole vocabulary a reader of music expects, so an exercise can be entered
 * without leaving the keyboard once it's mastered. The mouse stays the
 * on-ramp: every one of these has a clickable equivalent in the toolbar
 * above, which is what a first-time user reaches for.
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
      if (event.shiftKey) editor.extendSelectionLeft();
      else editor.moveLeft();
      return;
    case "ArrowRight":
      event.preventDefault();
      if (event.shiftKey) editor.extendSelectionRight();
      else editor.moveRight();
      return;
    case "Backspace":
      event.preventDefault();
      editor.deleteBefore();
      return;
    case "Delete":
      event.preventDefault();
      editor.deleteAtCursor();
      return;
    case ".":
      event.preventDefault();
      editor.setDots(editor.activeDots.value >= MAX_DOTS ? 0 : editor.activeDots.value + 1);
      return;
  }

  // Copy/paste/undo/redo are the shortcuts that keep their usual Ctrl/Cmd
  // modifier - overriding the browser's own versions on a page with a
  // notation editor on it would be more surprising than reusing them.
  if ((event.ctrlKey || event.metaKey) && !event.altKey) {
    const letter = event.key.toLowerCase();
    if (letter === "c") {
      event.preventDefault();
      editor.copySelection();
      return;
    }
    if (letter === "v") {
      event.preventDefault();
      editor.pasteAtCursor();
      return;
    }
    if (letter === "z") {
      event.preventDefault();
      if (event.shiftKey) editor.redo();
      else editor.undo();
      return;
    }
  }

  // Everything past this point is a bare letter or digit; a modifier held
  // down means the browser or OS owns this keystroke instead (Cmd+A
  // select-all shares a key with the pitch A, for one).
  if (event.ctrlKey || event.metaKey || event.altKey) return;

  const durationSpec = DURATIONS.find((spec) => spec.shortcut === event.key);
  if (durationSpec) {
    event.preventDefault();
    editor.setDuration(durationSpec.name);
    return;
  }

  const letter = event.key.toUpperCase();
  if (letter === "R") {
    event.preventDefault();
    editor.setRestMode(!editor.activeIsRest.value);
    return;
  }
  if (letter === "T") {
    event.preventDefault();
    editor.toggleTie();
    return;
  }
  if (letter === "K") {
    event.preventDefault();
    editor.toggleBeamBreak();
    return;
  }
  if (letter === "S") {
    event.preventDefault();
    editor.toggleSlur();
    return;
  }
  const articulation = ARTICULATION_SHORTCUT[letter];
  if (articulation) {
    event.preventDefault();
    editor.setArticulation(articulation);
    return;
  }
  if ((PITCH_STEPS as readonly string[]).includes(letter)) {
    event.preventDefault();
    editor.placeStep(letter as PitchStep);
  }
}
</script>

<template>
  <div class="flex flex-col gap-3" tabindex="0" @keydown="handleKeydown">
    <div class="flex flex-wrap items-center gap-4">
      <StaffSelector
        :staves="editor.document.value.staves"
        :active-staff-index="editor.cursor.value.staffIndex"
        :locked-staff-indices="props.lockedStaffIndices ?? []"
        @select="editor.setActiveStaff"
      />
      <VoiceSelector
        :voices="editor.activeStaffVoices.value"
        :active-voice-id="editor.cursor.value.voiceId"
        @select="editor.setActiveVoice"
      />
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
      <BeamToggle
        :active="editor.isBeamBrokenAtCursor.value"
        :disabled="!editor.canToggleBeamAtCursor.value"
        @toggle="editor.toggleBeamBreak"
      />
      <SlurToggle
        :active="editor.isSlurredAtCursor.value"
        :disabled="!editor.canSlurAtCursor.value"
        @toggle="editor.toggleSlur"
      />
      <ArticulationPalette
        :active="editor.articulationAtCursor.value"
        :disabled="!editor.canArticulateAtCursor.value"
        @select="editor.setArticulation"
      />
      <CopyPasteControls
        :can-copy="editor.canCopy.value"
        :can-paste="editor.canPaste.value"
        @copy="editor.copySelection"
        @paste="editor.pasteAtCursor"
      />
      <UndoRedoControls
        :can-undo="editor.canUndo.value"
        :can-redo="editor.canRedo.value"
        @undo="editor.undo"
        @redo="editor.redo"
      />
      <MeasureControls
        :count="editor.measureCount.value"
        :can-add="editor.canAddMeasure.value"
        :can-remove="editor.canRemoveMeasure.value"
        @add="editor.addMeasure"
        @remove="editor.removeMeasure"
      />
      <PlaybackTransport
        :is-playing="playback.isPlaying.value"
        :tempo="editor.document.value.tempo"
        @play="playback.play"
        @stop="playback.stop"
        @update:tempo="editor.setTempo"
      />
      <ExportControls :document="editor.document.value" />
    </div>

    <StaffRenderer
      :document="editor.document.value"
      :active-voice-id="editor.cursor.value.voiceId"
      :cursor-note-id="editor.cursorNoteId.value"
      :playing-note-ids="playback.activeNoteIds.value"
      :selected-note-ids="editor.selectedNoteIds.value"
      @staff-click="handleStaffClick"
    />

    <p v-if="editor.lastRefusal.value" class="text-sm text-amber-700" role="status">
      {{ editor.lastRefusal.value }}
    </p>
  </div>
</template>
