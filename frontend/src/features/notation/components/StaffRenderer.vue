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
import { Renderer, Stave } from "vexflow";

import { keySignatureName } from "../constants";
import { measureCount } from "../document";
import type { NotationDocument } from "../types";

const props = withDefaults(
  defineProps<{
    document: NotationDocument;
    /** Measures per system before wrapping. */
    measuresPerSystem?: number;
  }>(),
  { measuresPerSystem: 4 },
);

const host = ref<HTMLDivElement | null>(null);

const STAFF_HEIGHT = 100;
const SYSTEM_GAP = 30;
const PADDING_X = 10;
const PADDING_Y = 20;
/** Extra width for the first measure of a system, which carries the clef. */
const FIRST_MEASURE_EXTRA = 60;

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

function systemCount(): number {
  return Math.max(1, Math.ceil(measureCount(props.document) / props.measuresPerSystem));
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

  const total = measureCount(props.document);
  const perSystem = props.measuresPerSystem;
  const usableWidth = width - PADDING_X * 2;

  for (let measureIndex = 0; measureIndex < total; measureIndex += 1) {
    const systemIndex = Math.floor(measureIndex / perSystem);
    const columnIndex = measureIndex % perSystem;
    const inThisSystem = Math.min(perSystem, total - systemIndex * perSystem);

    // The first measure of a system is wider because the clef and key
    // signature live inside it; the rest share what's left evenly.
    const baseWidth = (usableWidth - FIRST_MEASURE_EXTRA) / inThisSystem;
    const measureWidth = columnIndex === 0 ? baseWidth + FIRST_MEASURE_EXTRA : baseWidth;
    const x =
      PADDING_X + (columnIndex === 0 ? 0 : FIRST_MEASURE_EXTRA + baseWidth * columnIndex);

    props.document.staves.forEach((staff, staffIndex) => {
      const y =
        PADDING_Y +
        systemIndex * (props.document.staves.length * STAFF_HEIGHT + SYSTEM_GAP) +
        staffIndex * STAFF_HEIGHT;

      const stave = new Stave(x, y, measureWidth);
      if (columnIndex === 0) {
        stave.addClef(staff.clef);
        stave.addKeySignature(keySignatureName(props.document.fifths));
        if (systemIndex === 0) {
          stave.addTimeSignature(`${props.document.time.beats}/${props.document.time.beatType}`);
        }
      }
      stave.setContext(context).draw();
      drawnStaves.push({ staffIndex, measureIndex, stave });
    });
  }
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

watch(() => props.document, draw, { deep: true });
watch(() => props.measuresPerSystem, draw);

defineExpose({ redraw: draw });
</script>

<template>
  <div ref="host" class="w-full overflow-x-auto rounded-md border border-slate-200 bg-white" />
</template>
