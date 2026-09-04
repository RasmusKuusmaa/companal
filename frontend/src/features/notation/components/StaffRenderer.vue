<script setup lang="ts">
/**
 * Draws a notation document with VexFlow.
 *
 * VexFlow rather than OpenSheetMusicDisplay, which this app already has:
 * OSMD renders MusicXML and offers no way to ask where a note *is* on the
 * page, which is exactly what an editor needs. VexFlow draws from a
 * JavaScript model and hands back the geometry, so a click can be turned
 * into a pitch.
 *
 * Redrawing is wholesale - the SVG is cleared and rebuilt on every change.
 * A student's exercise is a few dozen bars, so a full redraw is under a
 * frame, and incremental drawing would mean maintaining a second model of
 * what's currently on screen.
 */
import { onBeforeUnmount, onMounted, ref, watch } from "vue";
import { Barline, Formatter, Renderer, Stave, StaveTie, type StaveNote } from "vexflow";

import { keySignatureName } from "../constants";
import { measureCount } from "../document";
import { insertionIndexAtX, noteAtX, pitchAtY, staveAtPoint } from "../hit-test";
import type { NotationDocument, NotationNote, PitchStep } from "../types";
import { applyAccidentals, buildBeams, buildTies, buildVoice } from "../vexflow";

const props = withDefaults(
  defineProps<{
    document: NotationDocument;
    /** Measures per system before wrapping. */
    measuresPerSystem?: number;
    /** Which voice a click enters into, on staves that carry more than one. */
    activeVoiceId?: string;
  }>(),
  { measuresPerSystem: 4, activeVoiceId: undefined },
);

const emit = defineEmits<{
  /** A click resolved to a place on the staff. */
  (event: "staff-click", payload: StaffClick): void;
}>();

/** Everything a click means, resolved from raw coordinates. */
export interface StaffClick {
  staffIndex: number;
  measureIndex: number;
  voiceId: string;
  /** Where a new note would go in the voice. */
  insertionIndex: number;
  step: PitchStep;
  octave: number;
  /** The note actually clicked on, when the click landed on a head. */
  noteId: string | null;
}

const host = ref<HTMLDivElement | null>(null);

const STAFF_HEIGHT = 100;
const SYSTEM_GAP = 30;
const PADDING_X = 10;
/** Left gutter for part names, when any staff has one. */
const NAME_GUTTER = 64;
const PADDING_Y = 20;
/** Extra width for the first measure of a system, which carries the clef. */
const FIRST_MEASURE_EXTRA = 60;
/** Breathing room so notes don't sit against the barline. */
const NOTE_PADDING = 20;

let renderer: Renderer | null = null;
let resizeObserver: ResizeObserver | null = null;

/**
 * The drawn staves, kept outside Vue's reactivity.
 *
 * These are VexFlow objects holding canvas coordinates, and they exist so a
 * pointer position can be resolved back to a staff, a measure and a staff
 * line. Making them reactive would deep-proxy VexFlow's internals for no
 * benefit and a lot of overhead.
 */
export interface DrawnStave {
  staffIndex: number;
  measureIndex: number;
  stave: Stave;
}
let drawnStaves: DrawnStave[] = [];

/** Where each note ended up, so a click can find the note it landed on. */
export interface DrawnNote {
  note: NotationNote;
  staffIndex: number;
  measureIndex: number;
  voiceId: string;
  noteIndex: number;
  x: number;
  width: number;
}
let drawnNotes: DrawnNote[] = [];

/**
 * The last note of each voice from the previous measure, kept only long
 * enough to draw a tie into the first note of the next one.
 *
 * A tie within one measure is drawn from that measure's own note list (see
 * `buildTies`), but a tie held *over* a barline needs glyphs from two
 * measures that are built independently - this is what bridges them. Keyed
 * by `staffIndex:voiceId` since a voice's identity continues across
 * measures but its VexFlow objects don't.
 */
let tieTails = new Map<string, { note: NotationNote; staveNote: StaveNote }>();

function systemCount(): number {
  return Math.max(1, Math.ceil(measureCount(props.document) / props.measuresPerSystem));
}

/**
 * Draws every voice of one measure onto its stave.
 *
 * The voices of a measure are formatted together, not one after another, so
 * that a soprano crotchet and an alto minim starting on the same beat line
 * up vertically the way they must in a score.
 */
function drawMeasureNotes(
  context: ReturnType<Renderer["getContext"]>,
  stave: Stave,
  staffIndex: number,
  measureIndex: number,
): void {
  const staff = props.document.staves[staffIndex];
  const measure = staff?.measures[measureIndex];
  if (!staff || !measure) return;

  const built = measure.voices
    .filter((voice) => voice.notes.length > 0)
    .map((voice) => ({ voiceId: voice.id, ...buildVoice(props.document, voice, staff.clef) }));
  if (built.length === 0) return;

  const voices = built.map((entry) => entry.voice);
  applyAccidentals(props.document, voices);

  const formatter = new Formatter();
  formatter.joinVoices(voices);
  formatter.format(voices, stave.getNoteEndX() - stave.getNoteStartX() - NOTE_PADDING);

  for (const entry of built) {
    entry.voice.draw(context, stave);

    for (const beam of buildBeams(entry)) {
      beam.setContext(context).draw();
    }
    for (const tie of buildTies(entry)) {
      tie.setContext(context).draw();
    }

    const tailKey = `${staffIndex}:${entry.voiceId}`;
    const incomingTail = tieTails.get(tailKey);
    const firstNote = entry.notes[0];
    if (incomingTail?.note.tiedToNext && firstNote) {
      new StaveTie({
        firstNote: incomingTail.staveNote,
        lastNote: firstNote.staveNote,
        firstIndexes: [0],
        lastIndexes: [0],
      })
        .setContext(context)
        .draw();
    }

    entry.notes.forEach((drawn, noteIndex) => {
      // `getAbsoluteX`/`getWidth` rather than `getBoundingBox`: the bounding
      // box measures every attached glyph, which drags in canvas text
      // metrics. The head's x and width are all a hit test needs.
      drawnNotes.push({
        note: drawn.note,
        staffIndex,
        measureIndex,
        voiceId: entry.voiceId,
        noteIndex,
        x: drawn.staveNote.getAbsoluteX(),
        width: drawn.staveNote.getWidth(),
      });
    });

    const lastNote = entry.notes[entry.notes.length - 1];
    if (lastNote) tieTails.set(tailKey, lastNote);
  }
}

function draw(): void {
  const element = host.value;
  if (!element) return;

  const width = Math.max(element.clientWidth, 320);
  const staffCount = props.document.staves.length;
  const height =
    PADDING_Y * 2 + systemCount() * (staffCount * STAFF_HEIGHT + SYSTEM_GAP) - SYSTEM_GAP;

  if (!renderer) {
    renderer = new Renderer(element, Renderer.Backends.SVG);
  }
  renderer.resize(width, height);

  const context = renderer.getContext();
  context.clear();

  drawnStaves = [];
  drawnNotes = [];
  tieTails = new Map();

  const total = measureCount(props.document);
  const perSystem = props.measuresPerSystem;
  const hasNames = props.document.staves.some((staff) => staff.name);
  const gutter = hasNames ? NAME_GUTTER : 0;
  const usableWidth = width - PADDING_X * 2 - gutter;

  for (let measureIndex = 0; measureIndex < total; measureIndex += 1) {
    const systemIndex = Math.floor(measureIndex / perSystem);
    const columnIndex = measureIndex % perSystem;
    const inThisSystem = Math.min(perSystem, total - systemIndex * perSystem);

    // The first measure of a system is wider because the clef and key
    // signature live inside it; the rest share what's left evenly.
    const baseWidth = (usableWidth - FIRST_MEASURE_EXTRA) / inThisSystem;
    const measureWidth = columnIndex === 0 ? baseWidth + FIRST_MEASURE_EXTRA : baseWidth;
    const x =
      PADDING_X + gutter + (columnIndex === 0 ? 0 : FIRST_MEASURE_EXTRA + baseWidth * columnIndex);

    props.document.staves.forEach((staff, staffIndex) => {
      const y =
        PADDING_Y +
        systemIndex * (props.document.staves.length * STAFF_HEIGHT + SYSTEM_GAP) +
        staffIndex * STAFF_HEIGHT;

      const stave = new Stave(x, y, measureWidth);

      // Clef and key signature restate at the head of every system, the way
      // they do in print; the time signature appears once, at the start of
      // the piece, and only reappears if the metre actually changes.
      if (columnIndex === 0) {
        stave.addClef(staff.clef);
        stave.addKeySignature(keySignatureName(props.document.fifths));
        if (systemIndex === 0) {
          stave.addTimeSignature(`${props.document.time.beats}/${props.document.time.beatType}`);
        }
      }

      if (measureIndex === total - 1) {
        stave.setEndBarType(Barline.type.END);
      }

      stave.setContext(context).draw();

      drawMeasureNotes(context, stave, staffIndex, measureIndex);

      // Part names are drawn directly rather than through a stave modifier:
      // VexFlow 5 has no `Stave.setText`, and a label in the gutter is
      // simpler than a modifier that would also have to reserve its space.
      if (staff.name && columnIndex === 0) {
        context.save();
        context.setFont("system-ui, sans-serif", 11);
        context.fillText(staff.name, PADDING_X, y + STAFF_HEIGHT / 2 - 10);
        context.restore();
      }
      drawnStaves.push({ staffIndex, measureIndex, stave });
    });
  }
}

/**
 * Resolves a pointer event to a staff position.
 *
 * Coordinates come from the SVG's own bounding rect rather than the host
 * div, so scrolling the score horizontally doesn't shift every note by the
 * scroll offset.
 */
function handleClick(event: MouseEvent): void {
  const svg = host.value?.querySelector("svg");
  if (!svg) return;

  const rect = svg.getBoundingClientRect();
  const x = event.clientX - rect.left;
  const y = event.clientY - rect.top;

  const boxes = drawnStaves.map(({ staffIndex, measureIndex, stave }) => ({
    staffIndex,
    measureIndex,
    x: stave.getNoteStartX(),
    width: stave.getNoteEndX() - stave.getNoteStartX(),
    topLineY: stave.getYForLine(0),
    bottomLineY: stave.getYForLine(4),
    lineSpacing: stave.getSpacingBetweenLines(),
  }));

  const box = staveAtPoint(boxes, x, y);
  if (!box) return;

  const staff = props.document.staves[box.staffIndex];
  const measure = staff?.measures[box.measureIndex];
  if (!staff || !measure) return;

  // With one voice per staff the choice is made for us; multi-voice staves
  // take the voice the editor is currently on, which the parent supplies.
  const voiceId = props.activeVoiceId ?? measure.voices[0]?.id;
  if (!voiceId) return;

  const inVoice = drawnNotes.filter(
    (note) =>
      note.staffIndex === box.staffIndex &&
      note.measureIndex === box.measureIndex &&
      note.voiceId === voiceId,
  );

  const pitch = pitchAtY(
    { clef: staff.clef, topLineY: box.topLineY, lineSpacing: box.lineSpacing },
    y,
  );

  emit("staff-click", {
    staffIndex: box.staffIndex,
    measureIndex: box.measureIndex,
    voiceId,
    insertionIndex: insertionIndexAtX(inVoice, x),
    step: pitch.step,
    octave: pitch.octave,
    noteId: noteAtX(inVoice, x)?.note.id ?? null,
  });
}

onMounted(() => {
  draw();
  if (typeof ResizeObserver !== "undefined" && host.value) {
    resizeObserver = new ResizeObserver(() => draw());
    resizeObserver.observe(host.value);
  }
});

onBeforeUnmount(() => {
  resizeObserver?.disconnect();
  resizeObserver = null;
});

// Not a deep watch: documents are replaced rather than mutated (see the
// edit helpers in ../document), so identity changing is the signal.
watch(() => props.document, draw);
watch(() => props.measuresPerSystem, draw);

defineExpose({ redraw: draw, drawnStaves: () => drawnStaves, drawnNotes: () => drawnNotes });
</script>

<template>
  <div
    ref="host"
    class="w-full cursor-crosshair overflow-x-auto rounded-md border border-slate-200 bg-white"
    @click="handleClick"
  />
</template>
