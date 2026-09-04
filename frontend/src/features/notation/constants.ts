/**
 * The fixed vocabulary of the editor: note values, accidentals, clefs, keys.
 *
 * Quarter-note lengths are the unit throughout, matching music21's
 * `quarterLength` on the other side of the wire. Every value here is a
 * negative power of two scaled by a dot factor, so the arithmetic is exact
 * in binary floating point - no rounding tolerance is needed to decide
 * whether a bar is full. That stops being true the day tuplets arrive,
 * which is one reason they aren't here yet.
 */

import type { ClefName, DurationName, PitchStep } from "./types";

export interface DurationSpec {
  name: DurationName;
  /** Length in quarter notes, before dots. */
  quarters: number;
  /** VexFlow's duration code. */
  code: string;
  label: string;
  /** Keyboard shortcut, longest note to shortest. */
  shortcut: string;
}

export const DURATIONS: readonly DurationSpec[] = [
  { name: "whole", quarters: 4, code: "w", label: "Whole", shortcut: "1" },
  { name: "half", quarters: 2, code: "h", label: "Half", shortcut: "2" },
  { name: "quarter", quarters: 1, code: "q", label: "Quarter", shortcut: "3" },
  { name: "eighth", quarters: 0.5, code: "8", label: "Eighth", shortcut: "4" },
  { name: "16th", quarters: 0.25, code: "16", label: "Sixteenth", shortcut: "5" },
  { name: "32nd", quarters: 0.125, code: "32", label: "Thirty-second", shortcut: "6" },
] as const;

const DURATION_BY_NAME = new Map(DURATIONS.map((spec) => [spec.name, spec]));

export function durationSpec(name: DurationName): DurationSpec {
  const spec = DURATION_BY_NAME.get(name);
  if (!spec) throw new Error(`Unknown duration: ${name}`);
  return spec;
}

/**
 * Length of a note in quarters, dots included.
 *
 * Each dot adds half of what came before, so n dots multiply the base by
 * `2 - 2^-n`: one dot is 1.5×, two dots 1.75×.
 */
export function quarterLength(duration: DurationName, dots: number): number {
  return durationSpec(duration).quarters * (2 - Math.pow(2, -dots));
}

export const MAX_DOTS = 2;

export interface AccidentalSpec {
  /** Semitone offset from the natural. */
  alter: number;
  /** VexFlow's accidental code. */
  code: string;
  symbol: string;
  label: string;
}

/**
 * Double accidentals are included because this is an editor for classical
 * musicians: a raised leading tone in a minor key modulating sharpwards
 * needs a double sharp, and an editor that can't write one can't set
 * half the exercises in Stage 4.
 */
export const ACCIDENTALS: readonly AccidentalSpec[] = [
  { alter: -2, code: "bb", symbol: "𝄫", label: "Double flat" },
  { alter: -1, code: "b", symbol: "♭", label: "Flat" },
  { alter: 0, code: "n", symbol: "♮", label: "Natural" },
  { alter: 1, code: "#", symbol: "♯", label: "Sharp" },
  { alter: 2, code: "##", symbol: "𝄪", label: "Double sharp" },
] as const;

export function accidentalSpec(alter: number): AccidentalSpec | undefined {
  return ACCIDENTALS.find((spec) => spec.alter === alter);
}

/** Diatonic order within an octave; C is 0, matching scientific pitch notation. */
export const PITCH_STEPS: readonly PitchStep[] = ["C", "D", "E", "F", "G", "A", "B"] as const;

export const STEP_INDEX: Readonly<Record<PitchStep, number>> = {
  C: 0,
  D: 1,
  E: 2,
  F: 3,
  G: 4,
  A: 5,
  B: 6,
};

/** Semitones above C for each natural step - the major scale's own pattern. */
export const STEP_SEMITONES: Readonly<Record<PitchStep, number>> = {
  C: 0,
  D: 2,
  E: 4,
  F: 5,
  G: 7,
  A: 9,
  B: 11,
};

export interface ClefSpec {
  name: ClefName;
  label: string;
  /**
   * The pitch sitting on the staff's top line. Everything else follows by
   * counting diatonic steps downwards, which is the whole of the geometry
   * needed to turn a click into a note.
   *
   *   treble  top line F5   ·  lines E4 G4 B4 D5 F5
   *   bass    top line A3   ·  lines G2 B2 D3 F3 A3
   *   alto    top line G4   ·  middle C on the middle line
   *   tenor   top line E4   ·  middle C on the fourth line
   */
  topLineStep: PitchStep;
  topLineOctave: number;
}

export const CLEFS: readonly ClefSpec[] = [
  { name: "treble", label: "Treble", topLineStep: "F", topLineOctave: 5 },
  { name: "bass", label: "Bass", topLineStep: "A", topLineOctave: 3 },
  { name: "alto", label: "Alto", topLineStep: "G", topLineOctave: 4 },
  { name: "tenor", label: "Tenor", topLineStep: "E", topLineOctave: 4 },
] as const;

const CLEF_BY_NAME = new Map(CLEFS.map((spec) => [spec.name, spec]));

export function clefSpec(name: ClefName): ClefSpec {
  const spec = CLEF_BY_NAME.get(name);
  if (!spec) throw new Error(`Unknown clef: ${name}`);
  return spec;
}

/**
 * Key signature names by number of sharps (positive) or flats (negative).
 * Both modes are listed because the signature alone doesn't say which -
 * that's what `NotationDocument.mode` is for.
 */
export const KEY_SIGNATURES: readonly { fifths: number; major: string; minor: string }[] = [
  { fifths: -7, major: "Cb", minor: "Ab" },
  { fifths: -6, major: "Gb", minor: "Eb" },
  { fifths: -5, major: "Db", minor: "Bb" },
  { fifths: -4, major: "Ab", minor: "F" },
  { fifths: -3, major: "Eb", minor: "C" },
  { fifths: -2, major: "Bb", minor: "G" },
  { fifths: -1, major: "F", minor: "D" },
  { fifths: 0, major: "C", minor: "A" },
  { fifths: 1, major: "G", minor: "E" },
  { fifths: 2, major: "D", minor: "B" },
  { fifths: 3, major: "A", minor: "F#" },
  { fifths: 4, major: "E", minor: "C#" },
  { fifths: 5, major: "B", minor: "G#" },
  { fifths: 6, major: "F#", minor: "D#" },
  { fifths: 7, major: "C#", minor: "A#" },
] as const;

/** VexFlow names a key signature by its major tonic, whatever the mode. */
export function keySignatureName(fifths: number): string {
  return KEY_SIGNATURES.find((key) => key.fifths === fifths)?.major ?? "C";
}
