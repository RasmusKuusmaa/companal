/**
 * The notation document: what the editor edits and what gets submitted.
 *
 * Shaped to mirror MusicXML's own hierarchy - part → measure → voice → note -
 * because the backend turns this into MusicXML with music21, and a model
 * that disagrees with the target format only moves the awkwardness into the
 * converter.
 *
 * Measures are explicit rather than derived by accumulating durations. An
 * exercise that says "eight bars" needs eight bars that exist whether or
 * not they're full yet, a half-written bar has to be a legal state, and a
 * note that doesn't fit should be refused at the barline rather than
 * silently shunting everything after it.
 *
 * Pitch is stored as step + octave + alter rather than a MIDI number: F♯
 * and G♭ are the same key on a piano and different notes on a page, and an
 * editor for classical musicians cannot lose that distinction. `alter` is
 * the accidental in semitones (-2..2), independent of the key signature.
 */

export type PitchStep = "C" | "D" | "E" | "F" | "G" | "A" | "B";

/** A single-note performance mark. At most one per note. */
export type ArticulationKind = "staccato" | "accent" | "tenuto" | "marcato";

export type ClefName = "treble" | "bass" | "alto" | "tenor";

/** Note values, longest to shortest. Tuplets are deliberately not here yet. */
export type DurationName = "whole" | "half" | "quarter" | "eighth" | "16th" | "32nd";

export interface NotationNote {
  /** Stable across edits, so selection and rendering can address one note. */
  id: string;
  step: PitchStep;
  /** Scientific pitch notation - middle C is octave 4. */
  octave: number;
  /** Semitone offset from the natural: -2 (♭♭) to 2 (♯♯). */
  alter: number;
  duration: DurationName;
  /** 0, 1 or 2 augmentation dots. */
  dots: number;
  isRest: boolean;
  /** Tied into the following note. The tie's other end is implied. */
  tiedToNext: boolean;
  /**
   * Forces a beam break right after this note, overriding the automatic
   * beat-based grouping eighths-and-shorter otherwise get - splitting four
   * sixteenths into 2+2 instead of one beamed group, say.
   */
  beamBreakAfter: boolean;
  /**
   * Legato phrasing into the following note - unlike a tie, a slur
   * connects different pitches. The slur's other end is implied, the same
   * as `tiedToNext`'s.
   */
  slurToNext: boolean;
  /** At most one performance mark; `null` for none. */
  articulation: ArticulationKind | null;
}

export interface NotationVoice {
  /**
   * Voice number within the staff, "1" upwards - the same identifier the
   * voice keeps in every measure, which is what makes a soprano line
   * followable from bar to bar (and what MusicXML's <voice> means).
   */
  id: string;
  notes: NotationNote[];
}

export interface NotationMeasure {
  id: string;
  voices: NotationVoice[];
}

export interface NotationStaff {
  id: string;
  clef: ClefName;
  /** Shown in exercises that name their parts, e.g. "Soprano". */
  name?: string;
  measures: NotationMeasure[];
}

export interface TimeSignature {
  beats: number;
  beatType: number;
}

export interface NotationDocument {
  /**
   * Key signature in MusicXML's terms: number of sharps (positive) or flats
   * (negative) on the staff. Stored as fifths rather than a tonic name
   * because that's what the signature actually is - C major and A minor
   * are both 0, and `mode` is what tells them apart.
   */
  fifths: number;
  mode: "major" | "minor";
  time: TimeSignature;
  /** Quarter notes per minute. */
  tempo: number;
  staves: NotationStaff[];
}

/** Where the editing cursor is: one note position inside one voice. */
export interface NotationCursor {
  staffIndex: number;
  measureIndex: number;
  voiceId: string;
  /** Index into the voice's notes; equal to `notes.length` when at the end. */
  noteIndex: number;
}

/**
 * One actual note's position inside one voice - `noteIndex` addresses a note
 * directly (0..notes.length - 1), unlike `NotationCursor`'s "gap before this
 * index" indexing. Used for a selection's two ends, which each name a note
 * that exists rather than a place to insert one.
 */
export interface NotePosition {
  staffIndex: number;
  measureIndex: number;
  voiceId: string;
  noteIndex: number;
}
