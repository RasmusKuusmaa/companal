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
  diatonicIndex,
  fits,
  insertNote,
  locateNote,
  measureCount as countMeasures,
  measureQuarters,
  moveCursor,
  nearestOctaveForStep,
  noteAt,
  removeLastMeasure,
  setTempo as setDocumentTempo,
  toggleTieBefore,
} from "../document";
import type {
  DurationName,
  NotationCursor,
  NotationDocument,
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
}

export function useNotationEditor(
  initial?: NotationDocument,
  options: NotationEditorOptions = {},
) {
  const { minMeasures = 1, maxMeasures } = options;
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

  function setDocument(next: NotationDocument): void {
    document.value = toRaw(next);
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
    document.value = setDocumentTempo(document.value, quarterNotesPerMinute);
  }

  /** Ties (or unties) the note before the cursor to whatever follows it. */
  function toggleTie(): void {
    if (!canTieAtCursor.value) return;
    document.value = toggleTieBefore(document.value, cursor.value);
  }

  /** Selects an existing note by clicking it - the cursor lands just after it. */
  function selectNote(noteId: string): void {
    const located = locateNote(document.value, noteId);
    if (located) cursor.value = located;
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
    cursor.value = {
      staffIndex,
      measureIndex: cursor.value.measureIndex,
      voiceId: voice.id,
      noteIndex: voice.notes.length,
    };
  }

  function moveLeft(): void {
    cursor.value = moveCursor(document.value, cursor.value, -1);
  }

  function moveRight(): void {
    cursor.value = moveCursor(document.value, cursor.value, 1);
  }

  /** Backspace: removes the note the cursor sits after. */
  function deleteBefore(): void {
    const result = deleteNoteBefore(document.value, cursor.value);
    document.value = result.document;
    cursor.value = result.cursor;
  }

  /** Delete: removes the note the cursor sits before. */
  function deleteAtCursor(): void {
    const result = deleteNoteAt(document.value, cursor.value);
    document.value = result.document;
    cursor.value = result.cursor;
  }

  /** Adds an empty measure to the end of every staff. */
  function addMeasure(): void {
    if (!canAddMeasure.value) return;
    document.value = appendMeasure(document.value);
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
    document.value = next;

    const lastIndex = countMeasures(next) - 1;
    if (cursor.value.measureIndex > lastIndex) {
      const voice = next.staves[cursor.value.staffIndex]?.measures[lastIndex]?.voices.find(
        (candidate) => candidate.id === cursor.value.voiceId,
      );
      cursor.value = {
        ...cursor.value,
        measureIndex: lastIndex,
        noteIndex: voice?.notes.length ?? 0,
      };
    }
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
    document.value = result.document;
    cursor.value = result.cursor;
    lastRefusal.value = result.inserted ? "" : "That bar is full.";
    // One-shot: the next note goes back to "whatever the bar/key implies"
    // unless the student picks another accidental for it specifically.
    if (result.inserted) activeAlter.value = 0;
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
    setActiveStaff,
    moveLeft,
    moveRight,
    deleteBefore,
    deleteAtCursor,
    addMeasure,
    removeMeasure,
  };
}

export type NotationEditor = ReturnType<typeof useNotationEditor>;
