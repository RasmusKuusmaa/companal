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

    if (!fits(document.value, target, activeDuration.value, 0)) {
      lastRefusal.value = "That bar is full.";
      cursor.value = target;
      return false;
    }

    const note = createNote({
      step: placement.step,
      octave: placement.octave,
      duration: activeDuration.value,
    });

    const result = insertNote(document.value, target, note);
    document.value = result.document;
    cursor.value = result.cursor;
    lastRefusal.value = result.inserted ? "" : "That bar is full.";
    return result.inserted;
  }

  return {
    document,
    cursor,
    activeDuration,
    lastRefusal,
    staffCount,
    barQuarters,
    setDocument,
    setDuration,
    placeAt,
  };
}

export type NotationEditor = ReturnType<typeof useNotationEditor>;
