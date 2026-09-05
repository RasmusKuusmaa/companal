/**
 * Turning notation documents into VexFlow objects.
 *
 * Kept out of the renderer component so the translation can be tested
 * without mounting anything, and so the component is left doing layout and
 * drawing rather than two jobs at once.
 *
 * Accidentals are the subtle part. A note carries its true pitch (`alter`),
 * never "whether to print a sharp" - those are different questions, and the
 * second one depends on the key signature and on what has already happened
 * in the bar. `Accidental.applyAccidentals` answers it properly: it prints
 * the sharp on the first F♯ of a bar in C major, prints nothing for the
 * same note in D major, and prints a natural for an F in D major. Deciding
 * that ourselves would mean reimplementing a rule every engraver knows and
 * most implementations get subtly wrong.
 */

import { Accidental, Beam, Dot, Stem, StaveNote, StaveTie, Voice } from "vexflow";

import { CLEF_MIDDLE_LINE, durationSpec, keySignatureName } from "./constants";
import type { ClefName, NotationDocument, NotationNote, NotationVoice } from "./types";

/** VexFlow's pitch spelling: `f#/4`, `bb/3`, `c/4`. */
const ALTER_SUFFIX: Readonly<Record<number, string>> = {
  [-2]: "bb",
  [-1]: "b",
  [0]: "",
  [1]: "#",
  [2]: "##",
};

export function vexKey(note: NotationNote): string {
  const suffix = ALTER_SUFFIX[note.alter] ?? "";
  return `${note.step.toLowerCase()}${suffix}/${note.octave}`;
}

/**
 * A rest's vertical position on the staff.
 *
 * Rests have no pitch, but they do have a place: convention puts them on
 * the clef's middle line - `CLEF_MIDDLE_LINE`, the same reference keyboard
 * entry uses for its default octave, since both are "the middle of this
 * staff" by definition.
 */
function restKey(clef: ClefName): string {
  const middle = CLEF_MIDDLE_LINE[clef];
  return `${middle.step.toLowerCase()}/${middle.octave}`;
}

export function buildStaveNote(
  note: NotationNote,
  clef: ClefName,
  stemDirection?: number,
): StaveNote {
  const staveNote = new StaveNote({
    keys: [note.isRest ? restKey(clef) : vexKey(note)],
    duration: durationSpec(note.duration).code,
    ...(note.isRest ? { type: "r" } : {}),
    ...(stemDirection !== undefined ? { stemDirection } : {}),
    clef,
  });

  if (note.dots > 0) {
    Dot.buildAndAttach([staveNote], { all: true });
    // buildAndAttach adds one dot per call, so a double dot needs a second.
    for (let i = 1; i < note.dots; i += 1) {
      Dot.buildAndAttach([staveNote], { all: true });
    }
  }

  return staveNote;
}

/**
 * Stem direction for one voice among several sharing a staff.
 *
 * Standard engraving convention: the first voice (soprano over alto, tenor
 * over bass) stems up, every other voice stems down - alternating rather
 * than each note's own pitch deciding, which is what keeps two voices'
 * stems from colliding into the same space. A staff with only one voice
 * gets `undefined`, leaving VexFlow's own pitch-based default in place -
 * the right choice for an ordinary single-line staff.
 */
export function stemDirectionForVoice(voiceIndex: number, voiceCount: number): number | undefined {
  if (voiceCount <= 1) return undefined;
  return voiceIndex % 2 === 0 ? Stem.UP : Stem.DOWN;
}

export interface BuiltVoice {
  voice: Voice;
  /** Parallel to the voice's tickables, so a note id can find its glyph. */
  notes: { note: NotationNote; staveNote: StaveNote }[];
}

/**
 * Builds one VexFlow voice for one measure.
 *
 * `VoiceMode.SOFT` because a half-written bar is a normal state in an
 * editor - strict mode throws when the ticks don't add up, which would
 * mean the staff going blank the moment a student starts typing.
 */
export function buildVoice(
  document: NotationDocument,
  voice: NotationVoice,
  clef: ClefName,
  stemDirection?: number,
): BuiltVoice {
  const built = voice.notes.map((note) => ({
    note,
    staveNote: buildStaveNote(note, clef, stemDirection),
  }));

  const vfVoice = new Voice({
    numBeats: document.time.beats,
    beatValue: document.time.beatType,
  });
  vfVoice.setStrict(false);
  vfVoice.addTickables(built.map((entry) => entry.staveNote));

  return { voice: vfVoice, notes: built };
}

/** Adds the accidentals the key signature and the bar don't already imply. */
export function applyAccidentals(document: NotationDocument, voices: Voice[]): void {
  if (voices.length === 0) return;
  Accidental.applyAccidentals(voices, keySignatureName(document.fifths));
}

/**
 * Beams eighths and shorter, leaving quarters and longer alone.
 *
 * Split into chunks at every `beamBreakAfter` note before handing each one
 * to VexFlow - a forced break just means "don't let this note's own chunk
 * extend past it", which `generateBeams` still figures out beat-grouping
 * and rest/long-note breaks for on its own, exactly as it would for the
 * whole voice at once.
 */
export function buildBeams(built: BuiltVoice): Beam[] {
  const beams: Beam[] = [];
  let chunkStart = 0;

  built.notes.forEach((entry, index) => {
    const isLast = index === built.notes.length - 1;
    if (entry.note.beamBreakAfter || isLast) {
      const chunk = built.notes.slice(chunkStart, index + 1).map((e) => e.staveNote);
      beams.push(...Beam.generateBeams(chunk));
      chunkStart = index + 1;
    }
  });

  return beams;
}

/**
 * Ties within one measure.
 *
 * A tie into the next bar needs both bars' glyphs and so is drawn by the
 * renderer, which is the only thing that holds them all; this covers the
 * common case where both ends sit in the same measure.
 */
export function buildTies(built: BuiltVoice): StaveTie[] {
  const ties: StaveTie[] = [];
  built.notes.forEach((entry, index) => {
    const next = built.notes[index + 1];
    if (!entry.note.tiedToNext || !next) return;
    ties.push(
      new StaveTie({
        firstNote: entry.staveNote,
        lastNote: next.staveNote,
        firstIndexes: [0],
        lastIndexes: [0],
      }),
    );
  });
  return ties;
}
