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

import { computed, ref, shallowRef } from "vue";

import { createDocument, createNote, fits, insertNote, measureQuarters } from "../document";
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

export function useNotationEditor(initial?: NotationDocument) {
  /**
   * `shallowRef`, not `ref`. Every edit replaces the whole document, so deep
   * reactivity buys nothing - and it actively breaks things: a deeply
   * reactive document is a Proxy, and `structuredClone` refuses to clone
   * one, which is exactly what the edit helpers do. Keeping it shallow also
   * spares Vue from proxying every note in the score.
   */
  const document = shallowRef<NotationDocument>(initial ?? createDocument());
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
   * Set when a note can't be entered - a full bar, most often.
   *
   * Held as state rather than thrown because it isn't exceptional: running
   * out of room in a bar is a normal thing to do while writing music, and
   * the editor's job is to say so, not to fail.
   */
  const lastRefusal = ref("");

  const staffCount = computed(() => document.value.staves.length);
  const barQuarters = computed(() => measureQuarters(document.value.time));

  function setDocument(next: NotationDocument): void {
    document.value = next;
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
    lastRefusal,
    staffCount,
    barQuarters,
    setDocument,
    setDuration,
    setDots,
    setAlter,
    placeAt,
  };
}

export type NotationEditor = ReturnType<typeof useNotationEditor>;
