/**
 * The editing state of one score: the document, the cursor, and what the
 * next note will be.
 *
 * A composable rather than a Pinia store because it is genuinely local -
 * an exercise page has one editor, and a page comparing two attempts would
 * want two independent ones. Nothing outside the editor needs to reach in.
 *
 * The "active" values (duration, accidental, rest) are the editor's modal
 * state, and they persist across notes on purpose: entering six quavers
 * should be six clicks, not six pairs of clicks. That's how every notation
 * program behaves and what anyone who reads music will expect.
 */

import { computed, ref, shallowRef, toRaw } from "vue";

import { CLEF_MIDDLE_LINE } from "../constants";
import {
  appendMeasure,
  createDocument,
  createNote,
  deleteNoteAt,
  deleteNoteBefore,
  deleteNotes,
  diatonicIndex,
  fits,
  insertNote,
  locateNote,
  measureCount as countMeasures,
  measureQuarters,
  moveCursor,
  nearestOctaveForStep,
  noteAt,
  notesById,
  notesInRange,
  removeLastMeasure,
  setTempo as setDocumentTempo,
  toggleTieBefore,
} from "../document";
import type {
  DurationName,
  NotationCursor,
  NotationDocument,
  NotationNote,
  NotationVoice,
  NotePosition,
  PitchStep,
} from "../types";

export interface StaffPlacement {
  staffIndex: number;
  measureIndex: number;
  voiceId: string;
  insertionIndex: number;
  step: PitchStep;
  octave: number;
}

export interface NotationEditorOptions {
  /**
   * Bounds on how many measures the score may have. Set by a composition
   * task that names a bar count - "an 8-bar melody" - so the editor can't
   * drift away from what the brief actually asked for. Undefined means no
   * bound: free composition and the editor's own defaults have no reason
   * to enforce a length.
   */
  minMeasures?: number;
  maxMeasures?: number;
  /**
   * Staff indices whose content can't be changed - the given material for
   * a harmonization or counterpoint exercise (a given soprano, a cantus
   * firmus). Navigation still works on them - clicking, arrow keys,
   * selecting a note - only the mutating operations refuse, surfacing the
   * same `lastRefusal` a full bar does.
   */
  lockedStaffIndices?: number[];
}

const LOCKED_STAFF_MESSAGE = "This line is given and can't be edited.";

export function useNotationEditor(
  initial?: NotationDocument,
  options: NotationEditorOptions = {},
) {
  const { minMeasures = 1, maxMeasures, lockedStaffIndices = [] } = options;
  /**
   * `shallowRef`, not `ref`. Every edit replaces the whole document, so deep
   * reactivity buys nothing - and it actively breaks things: a deeply
   * reactive document is a Proxy, and `structuredClone` refuses to clone
   * one, which is exactly what the edit helpers do. Keeping it shallow also
   * spares Vue from proxying every note in the score.
   *
   * `toRaw` on the initial value because `initial` often *is* a reactive
   * Proxy already - when the caller is a `v-model`-bound prop, Vue wraps
   * even a plain object passed into that prop. `structuredClone` (used
   * throughout ../document to produce each edit's new document) refuses to
   * clone a Proxy outright, so the document has to be de-proxied the moment
   * it enters the editor, not discovered as a bug on the first edit.
   */
  const document = shallowRef<NotationDocument>(toRaw(initial ?? createDocument()));
  const cursor = ref<NotationCursor>({
    staffIndex: 0,
    measureIndex: 0,
    voiceId: document.value.staves[0]?.measures[0]?.voices[0]?.id ?? "1",
    noteIndex: 0,
  });

  const activeDuration = ref<DurationName>("quarter");
  const activeDots = ref(0);
  /**
   * The accidental the next placed note carries, as a semitone offset.
   * Zero means "no accidental of its own" - what the key signature and the
   * bar's earlier accidentals already imply, which is what most notes are.
   * It does not persist after one note: an accidental applies to the note
   * it's chosen for, not to a whole run the way duration does.
   */
  const activeAlter = ref(0);
  /**
   * Whether the next placed note is a rest.
   *
   * Persistent like duration, not one-shot like the accidental: a bar of
   * rests is entered as a run of clicks with rest mode held on, the same
   * way a run of eighths is entered with eighth-note duration held on.
   */
  const activeIsRest = ref(false);

  /**
   * Set when a note can't be entered - a full bar, most often.
   *
   * Held as state rather than thrown because it isn't exceptional: running
   * out of room in a bar is a normal thing to do while writing music, and
   * the editor's job is to say so, not to fail.
   */
  const lastRefusal = ref("");

  function isStaffLocked(staffIndex: number): boolean {
    return lockedStaffIndices.includes(staffIndex);
  }

  const staffCount = computed(() => document.value.staves.length);
  const barQuarters = computed(() => measureQuarters(document.value.time));
  const measureCount = computed(() => countMeasures(document.value));
  const canAddMeasure = computed(
    () => maxMeasures === undefined || measureCount.value < maxMeasures,
  );
  const canRemoveMeasure = computed(() => measureCount.value > minMeasures);

  /** The note the "tie" control acts on - whichever one the cursor sits after. */
  const noteBeforeCursor = computed(() =>
    noteAt(document.value, { ...cursor.value, noteIndex: cursor.value.noteIndex - 1 }),
  );
  const canTieAtCursor = computed(() => {
    const note = noteBeforeCursor.value;
    return note !== undefined && !note.isRest;
  });
  const isTiedAtCursor = computed(() => noteBeforeCursor.value?.tiedToNext ?? false);
  /** Which note to highlight, so the cursor is visible on the staff, not just internal state. */
  const cursorNoteId = computed(() => noteBeforeCursor.value?.id ?? null);

  /** The voices sharing the cursor's staff, for a voice selector to list. */
  const activeStaffVoices = computed<NotationVoice[]>(
    () =>
      document.value.staves[cursor.value.staffIndex]?.measures[cursor.value.measureIndex]
        ?.voices ?? [],
  );

  /**
   * The other end of a selection in progress - the anchor stays fixed while
   * the cursor (the selection's "focus") moves under a shift-click or a
   * shift-arrow. `null` means nothing is selected.
   */
  const selectionAnchor = ref<NotePosition | null>(null);

  /**
   * The note position the cursor sits just after - the same note
   * `noteBeforeCursor` names, addressed the way a selection's ends are
   * rather than the way rendering wants it. `undefined` right at the start
   * of a voice, where there's no note to anchor a selection to yet.
   */
  const focusPosition = computed<NotePosition | undefined>(() => {
    if (cursor.value.noteIndex <= 0) return undefined;
    return {
      staffIndex: cursor.value.staffIndex,
      measureIndex: cursor.value.measureIndex,
      voiceId: cursor.value.voiceId,
      noteIndex: cursor.value.noteIndex - 1,
    };
  });

  /** Every note currently selected - empty when nothing is. */
  const selectedNoteIds = computed<ReadonlySet<string>>(() => {
    if (!selectionAnchor.value || !focusPosition.value) return new Set();
    return new Set(notesInRange(document.value, selectionAnchor.value, focusPosition.value));
  });

  const hasSelection = computed(() => selectedNoteIds.value.size > 0);

  /**
   * What the last copy put on the clipboard - full notes, not ids, since
   * pasting has to work even after the originals have since been edited or
   * deleted. Scoped to this editor instance, the same as everything else
   * here: copying between two different exercises isn't something this
   * needs to support.
   */
  const copiedNotes = ref<NotationNote[]>([]);
  const canCopy = computed(() => hasSelection.value);
  const canPaste = computed(() => copiedNotes.value.length > 0);

  /**
   * Undo/redo as a stack of whole previous states (document + cursor),
   * not a log of inverse operations - the same choice `../document`'s own
   * "replace, don't mutate" design already implies. Capped so an
   * hours-long editing session doesn't grow it without bound.
   */
  const MAX_HISTORY = 100;
  interface HistoryEntry {
    document: NotationDocument;
    cursor: NotationCursor;
  }
  const undoStack = shallowRef<HistoryEntry[]>([]);
  const redoStack = shallowRef<HistoryEntry[]>([]);
  const canUndo = computed(() => undoStack.value.length > 0);
  const canRedo = computed(() => redoStack.value.length > 0);

  /**
   * Applies an edit's result, recording the state it replaces as an undo
   * step first - unless nothing actually changed, which every edit
   * helper in `../document` signals by returning the very same document
   * reference it was given, not a new one. A real edit always clears the
   * redo stack: redoing past it would resurrect a future that a new edit
   * has since made impossible.
   */
  function commit(nextDocument: NotationDocument, nextCursor: NotationCursor = cursor.value): void {
    if (nextDocument !== document.value) {
      const entry: HistoryEntry = { document: document.value, cursor: cursor.value };
      const grown = [...undoStack.value, entry];
      undoStack.value = grown.length > MAX_HISTORY ? grown.slice(grown.length - MAX_HISTORY) : grown;
      redoStack.value = [];
    }
    document.value = nextDocument;
    cursor.value = nextCursor;
  }

  /** Steps back to the state before the last edit, if there was one. */
  function undo(): void {
    const entry = undoStack.value[undoStack.value.length - 1];
    if (!entry) return;
    redoStack.value = [...redoStack.value, { document: document.value, cursor: cursor.value }];
    undoStack.value = undoStack.value.slice(0, -1);
    document.value = entry.document;
    cursor.value = entry.cursor;
    clearSelection();
  }

  /** Re-applies the edit undo just stepped back from, if there is one. */
  function redo(): void {
    const entry = redoStack.value[redoStack.value.length - 1];
    if (!entry) return;
    undoStack.value = [...undoStack.value, { document: document.value, cursor: cursor.value }];
    redoStack.value = redoStack.value.slice(0, -1);
    document.value = entry.document;
    cursor.value = entry.cursor;
    clearSelection();
  }

  /**
   * Replaces the document wholesale - the parent loading a starter score
   * or resetting an exercise, not an edit the student made. Starts a fresh
   * undo history rather than treating the swap as one more step in the old
   * document's: undoing back into a different exercise entirely would be
   * bizarre.
   */
  function setDocument(next: NotationDocument): void {
    document.value = toRaw(next);
    undoStack.value = [];
    redoStack.value = [];
    clearSelection();
  }

  function setDuration(duration: DurationName): void {
    activeDuration.value = duration;
  }

  function setDots(dots: number): void {
    activeDots.value = dots;
  }

  function setAlter(alter: number): void {
    activeAlter.value = alter;
  }

  function setRestMode(isRest: boolean): void {
    activeIsRest.value = isRest;
  }

  function setTempo(quarterNotesPerMinute: number): void {
    commit(setDocumentTempo(document.value, quarterNotesPerMinute));
  }

  /** Ties (or unties) the note before the cursor to whatever follows it. */
  function toggleTie(): void {
    if (!canTieAtCursor.value) return;
    if (isStaffLocked(cursor.value.staffIndex)) {
      lastRefusal.value = LOCKED_STAFF_MESSAGE;
      return;
    }
    commit(toggleTieBefore(document.value, cursor.value));
  }

  /** Selects an existing note by clicking it - the cursor lands just after it. */
  function selectNote(noteId: string): void {
    clearSelection();
    const located = locateNote(document.value, noteId);
    if (located) cursor.value = located;
  }

  /** Drops the current selection, if there is one, without moving the cursor. */
  function clearSelection(): void {
    selectionAnchor.value = null;
  }

  /**
   * Starts (if nothing is selected yet) or continues a selection, then
   * moves the cursor left/right the way a plain arrow key would - shift's
   * usual role in a text editor.
   */
  function extendSelectionLeft(): void {
    if (!selectionAnchor.value) selectionAnchor.value = focusPosition.value ?? null;
    cursor.value = moveCursor(document.value, cursor.value, -1);
  }

  function extendSelectionRight(): void {
    if (!selectionAnchor.value) selectionAnchor.value = focusPosition.value ?? null;
    cursor.value = moveCursor(document.value, cursor.value, 1);
  }

  /** Shift-click's equivalent of `selectNote` - extends rather than replaces the selection. */
  function extendSelectionToNote(noteId: string): void {
    const located = locateNote(document.value, noteId);
    if (!located) return;
    if (!selectionAnchor.value) selectionAnchor.value = focusPosition.value ?? null;
    cursor.value = located;
  }

  /**
   * Removes every selected note at once, then collapses the selection and
   * leaves the cursor where the range used to start - the same place
   * deleting a run of selected text in a text editor leaves the caret.
   */
  function deleteSelection(): void {
    const anchor = selectionAnchor.value;
    const focus = focusPosition.value;
    if (!anchor || !focus) return;

    if (isStaffLocked(anchor.staffIndex)) {
      lastRefusal.value = LOCKED_STAFF_MESSAGE;
      return;
    }

    const anchorIsEarlier =
      anchor.measureIndex < focus.measureIndex ||
      (anchor.measureIndex === focus.measureIndex && anchor.noteIndex <= focus.noteIndex);
    const start = anchorIsEarlier ? anchor : focus;

    commit(deleteNotes(document.value, anchor.staffIndex, anchor.voiceId, selectedNoteIds.value), {
      staffIndex: anchor.staffIndex,
      measureIndex: start.measureIndex,
      voiceId: anchor.voiceId,
      noteIndex: start.noteIndex,
    });
    clearSelection();
  }

  /** Copies every selected note onto this editor's clipboard, in order. */
  function copySelection(): void {
    const anchor = selectionAnchor.value;
    const focus = focusPosition.value;
    if (!anchor || !focus) return;

    const ids = notesInRange(document.value, anchor, focus);
    copiedNotes.value = notesById(document.value, anchor.staffIndex, anchor.voiceId, ids).map(
      (note) => structuredClone(note),
    );
  }

  /**
   * Inserts a fresh copy of every clipboard note at the cursor, one after
   * another - fresh copies, not the originals, so the same ids don't end up
   * twice in one document. Stops (rather than spilling into the next
   * measure) at the first one that doesn't fit, the same refusal every
   * other insertion gives; whatever did fit is still kept.
   */
  function pasteAtCursor(): void {
    if (copiedNotes.value.length === 0) return;
    if (isStaffLocked(cursor.value.staffIndex)) {
      lastRefusal.value = LOCKED_STAFF_MESSAGE;
      return;
    }

    let workingDocument = document.value;
    let workingCursor = cursor.value;
    let insertedCount = 0;

    for (const sourceNote of copiedNotes.value) {
      const note = createNote({
        step: sourceNote.step,
        octave: sourceNote.octave,
        alter: sourceNote.alter,
        duration: sourceNote.duration,
        dots: sourceNote.dots,
        isRest: sourceNote.isRest,
        tiedToNext: sourceNote.tiedToNext,
      });
      const result = insertNote(workingDocument, workingCursor, note);
      if (!result.inserted) break;
      workingDocument = result.document;
      workingCursor = result.cursor;
      insertedCount += 1;
    }

    if (insertedCount === 0) {
      lastRefusal.value = "That bar is full.";
      return;
    }

    commit(workingDocument, workingCursor);
    clearSelection();
    lastRefusal.value =
      insertedCount === copiedNotes.value.length
        ? ""
        : "Only part of what was copied fit; the rest was left out.";
  }

  /**
   * Switches keyboard and click entry to a different staff, landing at the
   * end of its first voice in the cursor's current measure.
   *
   * A plain focus move, not an edit - unlike clicking blank staff space
   * (`placeAt`), this never places a note, which is what makes it usable
   * to reach an empty second staff that has nothing on it yet to click.
   */
  function setActiveStaff(staffIndex: number): void {
    const measure = document.value.staves[staffIndex]?.measures[cursor.value.measureIndex];
    const voice = measure?.voices[0];
    if (!voice) return;
    clearSelection();
    cursor.value = {
      staffIndex,
      measureIndex: cursor.value.measureIndex,
      voiceId: voice.id,
      noteIndex: voice.notes.length,
    };
  }

  /**
   * Switches entry to a different voice on the cursor's current staff,
   * landing at the end of it - the same plain focus move as
   * `setActiveStaff`, and for the same reason: an empty voice has nothing
   * on it yet to click.
   */
  function setActiveVoice(voiceId: string): void {
    const voice = activeStaffVoices.value.find((candidate) => candidate.id === voiceId);
    if (!voice) return;
    clearSelection();
    cursor.value = { ...cursor.value, voiceId, noteIndex: voice.notes.length };
  }

  function moveLeft(): void {
    clearSelection();
    cursor.value = moveCursor(document.value, cursor.value, -1);
  }

  function moveRight(): void {
    clearSelection();
    cursor.value = moveCursor(document.value, cursor.value, 1);
  }

  /** Backspace: removes the note the cursor sits after, or the whole selection if there is one. */
  function deleteBefore(): void {
    if (hasSelection.value) {
      deleteSelection();
      return;
    }
    if (isStaffLocked(cursor.value.staffIndex)) {
      lastRefusal.value = LOCKED_STAFF_MESSAGE;
      return;
    }
    const result = deleteNoteBefore(document.value, cursor.value);
    commit(result.document, result.cursor);
  }

  /** Delete: removes the note the cursor sits before, or the whole selection if there is one. */
  function deleteAtCursor(): void {
    if (hasSelection.value) {
      deleteSelection();
      return;
    }
    if (isStaffLocked(cursor.value.staffIndex)) {
      lastRefusal.value = LOCKED_STAFF_MESSAGE;
      return;
    }
    const result = deleteNoteAt(document.value, cursor.value);
    commit(result.document, result.cursor);
  }

  /** Adds an empty measure to the end of every staff. */
  function addMeasure(): void {
    if (!canAddMeasure.value) return;
    commit(appendMeasure(document.value));
  }

  /**
   * Removes the last measure from every staff.
   *
   * If the cursor was sitting in the measure that just disappeared, it
   * moves to the end of the new last measure - the same place a text
   * cursor lands when the line it was on is deleted, rather than pointing
   * at a measure that no longer exists.
   */
  function removeMeasure(): void {
    if (!canRemoveMeasure.value) return;
    const next = removeLastMeasure(document.value);

    const lastIndex = countMeasures(next) - 1;
    let nextCursor = cursor.value;
    if (cursor.value.measureIndex > lastIndex) {
      const voice = next.staves[cursor.value.staffIndex]?.measures[lastIndex]?.voices.find(
        (candidate) => candidate.id === cursor.value.voiceId,
      );
      nextCursor = {
        ...cursor.value,
        measureIndex: lastIndex,
        noteIndex: voice?.notes.length ?? 0,
      };
    }
    commit(next, nextCursor);
  }

  /**
   * Enters a note by pitch letter at the cursor, choosing the octave
   * nearest to whatever the student just entered.
   *
   * With nothing before the cursor yet, the reference is the clef's middle
   * line rather than a fixed octave - the same anchor a freshly placed rest
   * uses - so the first letter typed into an empty bar lands in the middle
   * of the staff instead of wherever octave 4 happens to fall for that clef.
   */
  function placeStep(step: PitchStep): boolean {
    const staff = document.value.staves[cursor.value.staffIndex];
    if (!staff) return false;

    const reference = noteBeforeCursor.value
      ? diatonicIndex(noteBeforeCursor.value.step, noteBeforeCursor.value.octave)
      : diatonicIndex(
          CLEF_MIDDLE_LINE[staff.clef].step,
          CLEF_MIDDLE_LINE[staff.clef].octave,
        );

    return placeAt({
      staffIndex: cursor.value.staffIndex,
      measureIndex: cursor.value.measureIndex,
      voiceId: cursor.value.voiceId,
      insertionIndex: cursor.value.noteIndex,
      step,
      octave: nearestOctaveForStep(step, reference),
    });
  }

  /**
   * Enters a note where the student clicked.
   *
   * The click carries an exact pitch - the y position on the staff is
   * unambiguous - so nothing here has to guess an octave.
   */
  function placeAt(placement: StaffPlacement): boolean {
    const target: NotationCursor = {
      staffIndex: placement.staffIndex,
      measureIndex: placement.measureIndex,
      voiceId: placement.voiceId,
      noteIndex: placement.insertionIndex,
    };

    if (isStaffLocked(placement.staffIndex)) {
      lastRefusal.value = LOCKED_STAFF_MESSAGE;
      cursor.value = target;
      return false;
    }

    if (!fits(document.value, target, activeDuration.value, activeDots.value)) {
      lastRefusal.value = "That bar is full.";
      cursor.value = target;
      return false;
    }

    const note = createNote({
      step: placement.step,
      octave: placement.octave,
      alter: activeAlter.value,
      duration: activeDuration.value,
      dots: activeDots.value,
      isRest: activeIsRest.value,
    });

    const result = insertNote(document.value, target, note);
    commit(result.document, result.cursor);
    lastRefusal.value = result.inserted ? "" : "That bar is full.";
    // One-shot: the next note goes back to "whatever the bar/key implies"
    // unless the student picks another accidental for it specifically.
    if (result.inserted) {
      activeAlter.value = 0;
      clearSelection();
    }
    return result.inserted;
  }

  return {
    document,
    cursor,
    activeDuration,
    activeDots,
    activeAlter,
    activeIsRest,
    lastRefusal,
    staffCount,
    barQuarters,
    measureCount,
    canAddMeasure,
    canRemoveMeasure,
    canTieAtCursor,
    isTiedAtCursor,
    cursorNoteId,
    activeStaffVoices,
    selectedNoteIds,
    hasSelection,
    canCopy,
    canPaste,
    canUndo,
    canRedo,
    isStaffLocked,
    setDocument,
    setDuration,
    setDots,
    setAlter,
    setRestMode,
    setTempo,
    placeAt,
    placeStep,
    toggleTie,
    selectNote,
    clearSelection,
    extendSelectionLeft,
    extendSelectionRight,
    extendSelectionToNote,
    deleteSelection,
    copySelection,
    pasteAtCursor,
    undo,
    redo,
    setActiveStaff,
    setActiveVoice,
    moveLeft,
    moveRight,
    deleteBefore,
    deleteAtCursor,
    addMeasure,
    removeMeasure,
  };
}

export type NotationEditor = ReturnType<typeof useNotationEditor>;
