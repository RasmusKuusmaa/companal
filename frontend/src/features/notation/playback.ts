/**
 * Turning a notation document into a flat, timed schedule of pitches to
 * sound - the input WebAudio playback needs and nothing more.
 *
 * Kept free of the Web Audio API entirely, so the scheduling logic (what
 * plays when, how tied notes merge into one sounding event) can be tested
 * without an AudioContext, which jsdom doesn't provide anyway.
 */

import { STEP_SEMITONES, quarterLength } from "./constants";
import type { NotationDocument, NotationNote } from "./types";

/** MIDI note number - 60 is middle C, matching the General MIDI convention. */
export function midiNumber(note: NotationNote): number {
  return (note.octave + 1) * 12 + STEP_SEMITONES[note.step] + note.alter;
}

/** Equal temperament, A4 = 440Hz. */
export function frequencyHz(note: NotationNote): number {
  return 440 * Math.pow(2, (midiNumber(note) - 69) / 12);
}

export interface ScheduledNote {
  staffIndex: number;
  /** The measure the sounding event *starts* in - see the tie note below. */
  measureIndex: number;
  voiceId: string;
  noteIndex: number;
  /**
   * The id of the first note in the tie chain this event plays. A run of
   * tied notes sounds as one continuous tone, so it schedules as one entry
   * here - there is nothing for a listener to distinguish between the tied
   * notes, and nothing for the cursor highlight to do differently either.
   */
  noteId: string;
  startSeconds: number;
  durationSeconds: number;
  frequencyHz: number;
}

/**
 * Builds the playback schedule for one document.
 *
 * Each staff's voices play independently and simultaneously - a soprano and
 * alto voice in the same staff both start at the beginning, exactly as they
 * would sound performed together. Within one voice, notes play back to
 * back in written order; a tie chain merges into a single sounding event
 * spanning every tied note's duration, so the ear hears one held tone
 * rather than a re-attack at the barline.
 */
export function buildSchedule(document: NotationDocument): ScheduledNote[] {
  const secondsPerQuarter = 60 / document.tempo;
  const schedule: ScheduledNote[] = [];

  document.staves.forEach((staff, staffIndex) => {
    const voiceIds = new Set<string>();
    for (const measure of staff.measures) {
      for (const voice of measure.voices) voiceIds.add(voice.id);
    }

    for (const voiceId of voiceIds) {
      const flat: { note: NotationNote; measureIndex: number; noteIndex: number }[] = [];
      staff.measures.forEach((measure, measureIndex) => {
        const voice = measure.voices.find((candidate) => candidate.id === voiceId);
        voice?.notes.forEach((note, noteIndex) => flat.push({ note, measureIndex, noteIndex }));
      });

      let elapsedQuarters = 0;
      let i = 0;
      while (i < flat.length) {
        const first = flat[i];
        if (!first) break;

        let totalQuarters = quarterLength(first.note.duration, first.note.dots);
        let last = first;
        while (last.note.tiedToNext) {
          const next = flat[flat.indexOf(last) + 1];
          if (!next) break;
          totalQuarters += quarterLength(next.note.duration, next.note.dots);
          last = next;
        }

        if (!first.note.isRest) {
          schedule.push({
            staffIndex,
            measureIndex: first.measureIndex,
            voiceId,
            noteIndex: first.noteIndex,
            noteId: first.note.id,
            startSeconds: elapsedQuarters * secondsPerQuarter,
            durationSeconds: totalQuarters * secondsPerQuarter,
            frequencyHz: frequencyHz(first.note),
          });
        }

        elapsedQuarters += totalQuarters;
        i = flat.indexOf(last) + 1;
      }
    }
  });

  return schedule;
}

/** Total length of the piece, in seconds - when the transport should stop. */
export function scheduleDuration(schedule: ScheduledNote[]): number {
  return schedule.reduce(
    (max, entry) => Math.max(max, entry.startSeconds + entry.durationSeconds),
    0,
  );
}
