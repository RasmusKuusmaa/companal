/**
 * Reading and editing a notation document.
 *
 * Every function that changes something returns a new document rather than
 * mutating the one it was given. That costs a clone per keystroke - nothing
 * at the size of a student exercise - and buys two things worth more:
 * edits are pure functions that can be tested without a component, and
 * undo/redo becomes a stack of previous documents rather than a log of
 * inverse operations.
 *
 * The invariant everything here maintains is that a voice never holds more
 * than its measure's worth of notes. A bar that's too full is not a state
 * the editor can reach, so nothing downstream - playback, MusicXML export,
 * the grader - has to cope with one.
 */

import { quarterLength } from "./constants";
import type {
  ClefName,
  DurationName,
  NotationCursor,
  NotationDocument,
  NotationMeasure,
  NotationNote,
  NotationStaff,
  NotationVoice,
  PitchStep,
  TimeSignature,
} from "./types";

let fallbackId = 0;

/**
 * `crypto.randomUUID` where it exists, a counter otherwise. Ids only have
 * to be unique within one document, so the fallback is sufficient for test
 * environments that don't implement the Web Crypto API.
 */
function newId(): string {
  if (typeof crypto !== "undefined" && typeof crypto.randomUUID === "function") {
    return crypto.randomUUID();
  }
  fallbackId += 1;
  return `n${fallbackId}`;
}

export function createNote(overrides: Partial<NotationNote> = {}): NotationNote {
  return {
    id: newId(),
    step: "C",
    octave: 4,
    alter: 0,
    duration: "quarter",
    dots: 0,
    isRest: false,
    tiedToNext: false,
    ...overrides,
  };
}

export function createVoice(id: string, notes: NotationNote[] = []): NotationVoice {
  return { id, notes };
}

export function createMeasure(voiceIds: string[]): NotationMeasure {
  return { id: newId(), voices: voiceIds.map((id) => createVoice(id)) };
}

export interface CreateDocumentOptions {
  clefs?: ClefName[];
  fifths?: number;
  mode?: "major" | "minor";
  time?: TimeSignature;
  tempo?: number;
  measureCount?: number;
  /** Voices per staff - 1 for a melody, 2 per staff for SATB. */
  voicesPerStaff?: number;
  staffNames?: string[];
}

export function createDocument(options: CreateDocumentOptions = {}): NotationDocument {
  const {
    clefs = ["treble"],
    fifths = 0,
    mode = "major",
    time = { beats: 4, beatType: 4 },
    tempo = 90,
    measureCount = 4,
    voicesPerStaff = 1,
    staffNames = [],
  } = options;

  // Voice numbers run across the whole part in MusicXML, not per staff, so
  // a grand staff's lower voices continue the numbering rather than
  // restarting - otherwise soprano and tenor would both be voice "1".
  let nextVoiceNumber = 1;
  const staves: NotationStaff[] = clefs.map((clef, staffIndex) => {
    const voiceIds: string[] = [];
    for (let i = 0; i < voicesPerStaff; i += 1) {
      voiceIds.push(String(nextVoiceNumber));
      nextVoiceNumber += 1;
    }
    const measures: NotationMeasure[] = [];
    for (let i = 0; i < measureCount; i += 1) {
      measures.push(createMeasure(voiceIds));
    }
    const name = staffNames[staffIndex];
    return { id: newId(), clef, ...(name ? { name } : {}), measures };
  });

  return { fifths, mode, time, tempo, staves };
}

/** Quarter notes in one measure of this time signature. */
export function measureQuarters(time: TimeSignature): number {
  return time.beats * (4 / time.beatType);
}

export function noteQuarters(note: NotationNote): number {
  return quarterLength(note.duration, note.dots);
}

export function voiceQuarters(voice: NotationVoice): number {
  return voice.notes.reduce((total, note) => total + noteQuarters(note), 0);
}

export function measureCount(document: NotationDocument): number {
  return document.staves[0]?.measures.length ?? 0;
}

export function getStaff(
  document: NotationDocument,
  staffIndex: number,
): NotationStaff | undefined {
  return document.staves[staffIndex];
}

export function getMeasure(
  document: NotationDocument,
  staffIndex: number,
  measureIndex: number,
): NotationMeasure | undefined {
  return document.staves[staffIndex]?.measures[measureIndex];
}

export function getVoice(
  document: NotationDocument,
  cursor: Pick<NotationCursor, "staffIndex" | "measureIndex" | "voiceId">,
): NotationVoice | undefined {
  return getMeasure(document, cursor.staffIndex, cursor.measureIndex)?.voices.find(
    (voice) => voice.id === cursor.voiceId,
  );
}

export function noteAt(
  document: NotationDocument,
  cursor: NotationCursor,
): NotationNote | undefined {
  return getVoice(document, cursor)?.notes[cursor.noteIndex];
}

/** Quarters still free in the cursor's measure for its voice. */
export function remainingQuarters(document: NotationDocument, cursor: NotationCursor): number {
  const voice = getVoice(document, cursor);
  if (!voice) return 0;
  return measureQuarters(document.time) - voiceQuarters(voice);
}

/** Whether a note of this length would still fit in the cursor's measure. */
export function fits(
  document: NotationDocument,
  cursor: NotationCursor,
  duration: DurationName,
  dots: number,
): boolean {
  return quarterLength(duration, dots) <= remainingQuarters(document, cursor) + 1e-9;
}

function clone(document: NotationDocument): NotationDocument {
  return structuredClone(document);
}

/**
 * Inserts a note at the cursor and returns the cursor position after it.
 *
 * Refuses rather than overflows: if the note doesn't fit in the bar, the
 * document comes back unchanged and `inserted` is false. Callers decide
 * what to tell the student - the alternative, spilling into the next
 * measure, would quietly rewrite music they didn't write.
 */
export function insertNote(
  document: NotationDocument,
  cursor: NotationCursor,
  note: NotationNote,
): { document: NotationDocument; cursor: NotationCursor; inserted: boolean } {
  if (!fits(document, cursor, note.duration, note.dots)) {
    return { document, cursor, inserted: false };
  }

  const next = clone(document);
  const voice = getVoice(next, cursor);
  if (!voice) return { document, cursor, inserted: false };

  const index = Math.min(Math.max(cursor.noteIndex, 0), voice.notes.length);
  voice.notes.splice(index, 0, note);

  return {
    document: next,
    cursor: { ...cursor, noteIndex: index + 1 },
    inserted: true,
  };
}

/** Replaces the note under the cursor, if the replacement still fits. */
export function replaceNote(
  document: NotationDocument,
  cursor: NotationCursor,
  changes: Partial<NotationNote>,
): NotationDocument {
  const existing = noteAt(document, cursor);
  if (!existing) return document;

  const updated = { ...existing, ...changes };
  const voice = getVoice(document, cursor);
  if (!voice) return document;

  const without = voiceQuarters(voice) - noteQuarters(existing);
  if (without + noteQuarters(updated) > measureQuarters(document.time) + 1e-9) {
    return document;
  }

  const next = clone(document);
  const nextVoice = getVoice(next, cursor);
  if (!nextVoice) return document;
  nextVoice.notes[cursor.noteIndex] = updated;
  return next;
}

/**
 * Toggles the tie on the note just before the cursor - the note the student
 * most recently placed or navigated to.
 *
 * A tie is a property of the note it starts from (`tiedToNext`), and its
 * partner is whatever note follows, in this measure or the next - the
 * renderer resolves that at draw time. Rests can't be tied, and toggling on
 * one is a no-op rather than an error: nothing about picking "tie" while
 * sitting on a rest should look like it worked.
 */
export function toggleTieBefore(
  document: NotationDocument,
  cursor: NotationCursor,
): NotationDocument {
  const target = { ...cursor, noteIndex: cursor.noteIndex - 1 };
  const note = noteAt(document, target);
  if (!note || note.isRest) return document;
  return replaceNote(document, target, { tiedToNext: !note.tiedToNext });
}

/** Deletes the note before the cursor, the way backspace behaves in text. */
export function deleteNoteBefore(
  document: NotationDocument,
  cursor: NotationCursor,
): { document: NotationDocument; cursor: NotationCursor } {
  if (cursor.noteIndex <= 0) return { document, cursor };

  const next = clone(document);
  const voice = getVoice(next, cursor);
  if (!voice) return { document, cursor };

  voice.notes.splice(cursor.noteIndex - 1, 1);
  return { document: next, cursor: { ...cursor, noteIndex: cursor.noteIndex - 1 } };
}

/** Deletes the note under the cursor, the way delete behaves in text. */
export function deleteNoteAt(
  document: NotationDocument,
  cursor: NotationCursor,
): { document: NotationDocument; cursor: NotationCursor } {
  const voice = getVoice(document, cursor);
  if (!voice || cursor.noteIndex >= voice.notes.length) return { document, cursor };

  const next = clone(document);
  const nextVoice = getVoice(next, cursor);
  if (!nextVoice) return { document, cursor };

  nextVoice.notes.splice(cursor.noteIndex, 1);
  return { document: next, cursor };
}

/**
 * Moves the cursor by whole notes, stepping across barlines.
 *
 * Crossing a barline lands *after* the last note of the previous measure
 * rather than on it, so walking left and right returns to where it started.
 */
export function moveCursor(
  document: NotationDocument,
  cursor: NotationCursor,
  delta: number,
): NotationCursor {
  let { measureIndex, noteIndex } = cursor;
  const staff = getStaff(document, cursor.staffIndex);
  if (!staff) return cursor;

  let remaining = Math.abs(delta);
  const step = Math.sign(delta);

  while (remaining > 0) {
    const voice = getVoice(document, { ...cursor, measureIndex });
    const length = voice?.notes.length ?? 0;

    if (step > 0) {
      if (noteIndex < length) {
        noteIndex += 1;
      } else if (measureIndex + 1 < staff.measures.length) {
        measureIndex += 1;
        noteIndex = 0;
      } else {
        break;
      }
    } else {
      if (noteIndex > 0) {
        noteIndex -= 1;
      } else if (measureIndex > 0) {
        measureIndex -= 1;
        const previous = getVoice(document, { ...cursor, measureIndex });
        noteIndex = previous?.notes.length ?? 0;
      } else {
        break;
      }
    }
    remaining -= 1;
  }

  return { ...cursor, measureIndex, noteIndex };
}

export function appendMeasure(document: NotationDocument): NotationDocument {
  const next = clone(document);
  for (const staff of next.staves) {
    const voiceIds = staff.measures[0]?.voices.map((voice) => voice.id) ?? ["1"];
    staff.measures.push(createMeasure(voiceIds));
  }
  return next;
}

/** Removes the last measure. The document always keeps at least one. */
export function removeLastMeasure(document: NotationDocument): NotationDocument {
  if (measureCount(document) <= 1) return document;
  const next = clone(document);
  for (const staff of next.staves) {
    staff.measures.pop();
  }
  return next;
}

/** Diatonic position: C4 is 28, D4 is 29 - accidentals don't move it. */
export function diatonicIndex(step: PitchStep, octave: number): number {
  const index = { C: 0, D: 1, E: 2, F: 3, G: 4, A: 5, B: 6 }[step];
  return octave * 7 + index;
}

export function fromDiatonicIndex(index: number): { step: PitchStep; octave: number } {
  const steps: PitchStep[] = ["C", "D", "E", "F", "G", "A", "B"];
  const octave = Math.floor(index / 7);
  const step = steps[((index % 7) + 7) % 7];
  return { step: step ?? "C", octave };
}
