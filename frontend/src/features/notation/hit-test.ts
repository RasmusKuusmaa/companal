/**
 * Turning a point on the page into a place in the music.
 *
 * All of it is geometry on the staff, and all of it is pure - the renderer
 * supplies the coordinates it drew at, and these functions say what was
 * clicked. Keeping the arithmetic here rather than inside the component
 * means the mapping can be tested without a DOM, which matters because
 * off-by-one errors in it are invisible until someone enters a wrong note.
 */

import { STEP_INDEX, clefSpec } from "./constants";
import { fromDiatonicIndex } from "./document";
import type { ClefName, PitchStep } from "./types";

/**
 * How far above and below the staff a click still counts, in half-lines.
 *
 * Four ledger lines either way - enough for the range any of these
 * exercises asks for, and short of the point where a stray click at the
 * edge of the canvas would silently enter a note three octaves out.
 */
const MAX_HALF_STEPS_ABOVE = 8;
const MAX_HALF_STEPS_BELOW = 24;

export interface StaffGeometry {
  clef: ClefName;
  /** Canvas y of the staff's top line. */
  topLineY: number;
  /** Distance between adjacent staff lines. */
  lineSpacing: number;
}

/**
 * The pitch at a vertical position.
 *
 * Every line and space is one diatonic step, so the whole conversion is:
 * measure the distance from the top line in half-line units, round to the
 * nearest, and count that many steps down the scale from the pitch the top
 * line carries. Accidentals never enter into it - where a note sits on the
 * staff says F, and whether that F is sharp is the key signature's business
 * or the student's.
 */
export function pitchAtY(geometry: StaffGeometry, y: number): { step: PitchStep; octave: number } {
  const spec = clefSpec(geometry.clef);
  const halfSpace = geometry.lineSpacing / 2;
  const raw = Math.round((y - geometry.topLineY) / halfSpace);
  const halfSteps = Math.min(Math.max(raw, -MAX_HALF_STEPS_ABOVE), MAX_HALF_STEPS_BELOW);

  const topDiatonic = spec.topLineOctave * 7 + STEP_INDEX[spec.topLineStep];
  return fromDiatonicIndex(topDiatonic - halfSteps);
}

/** Inverse of `pitchAtY` - where a pitch sits, for drawing a cursor. */
export function yForPitch(geometry: StaffGeometry, step: PitchStep, octave: number): number {
  const spec = clefSpec(geometry.clef);
  const topDiatonic = spec.topLineOctave * 7 + STEP_INDEX[spec.topLineStep];
  const halfSteps = topDiatonic - (octave * 7 + STEP_INDEX[step]);
  return geometry.topLineY + halfSteps * (geometry.lineSpacing / 2);
}

export interface StaveBox {
  staffIndex: number;
  measureIndex: number;
  x: number;
  width: number;
  topLineY: number;
  bottomLineY: number;
  lineSpacing: number;
}

/**
 * Which measure a point falls in.
 *
 * The vertical test is generous - half a staff's height above and below -
 * so that clicking a ledger-line note still lands on the staff it belongs
 * to rather than missing entirely. Horizontally it's exact, because two
 * measures sit side by side and guessing between them would be worse than
 * ignoring the click.
 */
export function staveAtPoint(boxes: StaveBox[], x: number, y: number): StaveBox | undefined {
  const candidates = boxes.filter((box) => x >= box.x && x <= box.x + box.width);
  if (candidates.length === 0) return undefined;

  let best: StaveBox | undefined;
  let bestDistance = Number.POSITIVE_INFINITY;

  for (const box of candidates) {
    const slack = (box.bottomLineY - box.topLineY) / 2;
    if (y < box.topLineY - slack || y > box.bottomLineY + slack) continue;

    const centre = (box.topLineY + box.bottomLineY) / 2;
    const distance = Math.abs(y - centre);
    if (distance < bestDistance) {
      best = box;
      bestDistance = distance;
    }
  }

  return best;
}

export interface NoteBox {
  staffIndex: number;
  measureIndex: number;
  voiceId: string;
  noteIndex: number;
  x: number;
  width: number;
}

/**
 * Where in a voice a click at this x belongs.
 *
 * Returns an insertion index, not a note: clicking on the left half of a
 * note means "before this one", the right half means "after". That's what
 * makes clicking between two notes insert between them rather than
 * replacing whichever was nearest.
 */
export function insertionIndexAtX(notes: NoteBox[], x: number): number {
  const ordered = [...notes].sort((a, b) => a.x - b.x);
  let index = 0;
  for (const note of ordered) {
    if (x < note.x + note.width / 2) return index;
    index += 1;
  }
  return index;
}

/**
 * The note whose head the point is actually on, for selection.
 *
 * Generic over the caller's own note type so the renderer gets back its own
 * richer record - with the document note attached - rather than the bare
 * geometry this module needs.
 */
export function noteAtX<T extends NoteBox>(notes: T[], x: number): T | undefined {
  return notes.find((note) => x >= note.x && x <= note.x + Math.max(note.width, 10));
}
