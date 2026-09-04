/**
 * Schedules a notation document's notes onto the Web Audio API and plays
 * them back.
 *
 * No synth library: a plain oscillator per note, shaped by a short envelope
 * so notes don't click at their edges, is everything a student needs to
 * hear what they wrote. Anything richer (sampled instruments, real timbre)
 * is a product decision for later, not a gap in this phase - the point of
 * playback here is proofreading a score, not a listening experience.
 *
 * Every note gets scheduled up front, all at once, using the AudioContext's
 * own clock (`ctx.currentTime` plus an offset) rather than a `setTimeout`
 * per note. `setTimeout` drifts under load and pauses in a backgrounded
 * tab; the audio clock doesn't, so a bar of sixteenth notes still lands on
 * the beat.
 */

import { onBeforeUnmount, type Ref, ref, shallowRef, watch } from "vue";

import { buildSchedule, scheduleDuration } from "../playback";
import type { NotationDocument } from "../types";

/** Seconds of linear ramp at a note's start and end, to avoid a click. */
const ENVELOPE_SECONDS = 0.015;
/** How far past 0 gain the sustain sits - quiet enough that a chord doesn't clip. */
const PEAK_GAIN = 0.25;

export function useNotationPlayback(document: Ref<NotationDocument>) {
  const isPlaying = ref(false);
  /** Seconds into the piece, updated on an animation frame while playing. */
  const currentTime = ref(0);
  /** Notes sounding right now, for the renderer's cursor highlight. */
  const activeNoteIds = shallowRef<Set<string>>(new Set());

  let audioContext: AudioContext | null = null;
  let startedAtContextTime = 0;
  let animationFrame: number | null = null;
  let activeNodes: { oscillator: OscillatorNode; gain: GainNode }[] = [];

  function getAudioContext(): AudioContext {
    audioContext ??= new AudioContext();
    return audioContext;
  }

  /**
   * Schedules one note's tone: ramp up, hold, ramp down, so the amplitude
   * is never discontinuous at either edge - a bare on/off gain produces an
   * audible click on every single note.
   */
  function scheduleTone(ctx: AudioContext, startAt: number, endAt: number, frequency: number): void {
    const oscillator = ctx.createOscillator();
    const gain = ctx.createGain();
    oscillator.type = "sine";
    oscillator.frequency.value = frequency;
    oscillator.connect(gain);
    gain.connect(ctx.destination);

    const rampEnd = Math.min(startAt + ENVELOPE_SECONDS, endAt);
    const rampStart = Math.max(endAt - ENVELOPE_SECONDS, rampEnd);

    gain.gain.setValueAtTime(0, startAt);
    gain.gain.linearRampToValueAtTime(PEAK_GAIN, rampEnd);
    gain.gain.setValueAtTime(PEAK_GAIN, rampStart);
    gain.gain.linearRampToValueAtTime(0, endAt);

    oscillator.start(startAt);
    oscillator.stop(endAt);
    activeNodes.push({ oscillator, gain });
  }

  function tick(): void {
    const ctx = audioContext;
    if (!ctx || !isPlaying.value) return;

    const elapsed = ctx.currentTime - startedAtContextTime;
    currentTime.value = elapsed;

    const schedule = buildSchedule(document.value);
    const sounding = new Set<string>();
    for (const entry of schedule) {
      if (elapsed >= entry.startSeconds && elapsed < entry.startSeconds + entry.durationSeconds) {
        sounding.add(entry.noteId);
      }
    }
    activeNoteIds.value = sounding;

    if (elapsed >= scheduleDuration(schedule)) {
      stop();
      return;
    }

    animationFrame = requestAnimationFrame(tick);
  }

  function play(): void {
    if (isPlaying.value) return;

    const schedule = buildSchedule(document.value);
    if (schedule.length === 0) return;

    const ctx = getAudioContext();
    startedAtContextTime = ctx.currentTime;

    for (const entry of schedule) {
      scheduleTone(
        ctx,
        startedAtContextTime + entry.startSeconds,
        startedAtContextTime + entry.startSeconds + entry.durationSeconds,
        entry.frequencyHz,
      );
    }

    isPlaying.value = true;
    currentTime.value = 0;
    animationFrame = requestAnimationFrame(tick);
  }

  function stop(): void {
    for (const { oscillator, gain } of activeNodes) {
      // `cancelScheduledValues` first - stopping an oscillator whose gain
      // ramp is still pending otherwise lets that ramp fire after the
      // context has moved on, and a residual gain change with nothing
      // making sound is a silent no-op but leaves the node's state ambiguous
      // to reason about, so it's cleaner to stop it outright.
      gain.gain.cancelScheduledValues(0);
      try {
        oscillator.stop();
      } catch {
        // Already stopped (it reached its own scheduled end) - fine.
      }
    }
    activeNodes = [];

    if (animationFrame !== null) {
      cancelAnimationFrame(animationFrame);
      animationFrame = null;
    }

    isPlaying.value = false;
    currentTime.value = 0;
    activeNoteIds.value = new Set();
  }

  // Editing the score mid-playback would otherwise keep sounding whatever
  // was scheduled against the old document - stopping is the only choice
  // that can't play something the student can no longer see on the staff.
  watch(document, () => {
    if (isPlaying.value) stop();
  });

  onBeforeUnmount(() => {
    stop();
    audioContext?.close().catch(() => {});
  });

  return { isPlaying, currentTime, activeNoteIds, play, stop };
}

export type NotationPlayback = ReturnType<typeof useNotationPlayback>;
