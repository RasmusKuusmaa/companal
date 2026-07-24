<script setup lang="ts">
import { OpenSheetMusicDisplay } from "opensheetmusicdisplay";
import { onBeforeUnmount, onMounted, ref, watch } from "vue";

const MIN_ZOOM = 0.25;

const props = defineProps<{
  file: Blob | null;
  zoom: number;
  page: number;
}>();

const emit = defineEmits<{
  loaded: [pageCount: number];
  error: [message: string];
  "update:zoom": [value: number];
}>();

const containerEl = ref<HTMLElement | null>(null);
const isRendering = ref(false);

let osmd: OpenSheetMusicDisplay | null = null;
let resizeObserver: ResizeObserver | null = null;
let resizeTimeout: ReturnType<typeof setTimeout> | null = null;

function pageElementIds(count: number): string[] {
  return Array.from({ length: count }, (_, index) => `osmdCanvasPage${index + 1}`);
}

function applyPageVisibility(pageCount: number, page: number): void {
  if (!containerEl.value) return;
  const current = Math.min(Math.max(page, 1), Math.max(pageCount, 1));
  for (const [index, id] of pageElementIds(pageCount).entries()) {
    const pageEl = containerEl.value.querySelector<HTMLElement>(`#${id}`);
    if (pageEl) {
      pageEl.style.display = index + 1 === current ? "" : "none";
    }
  }
}

/** Shrinks (never grows) zoom so the current page's rendered width fits the container, since a
 *  fixed page format doesn't scale to the container the way OSMD's default endless layout would. */
function fitToContainer(): void {
  if (!containerEl.value || !osmd) return;
  const available = containerEl.value.clientWidth;
  const contentWidth = containerEl.value.scrollWidth;
  if (available <= 0 || contentWidth <= available) return;

  const nextZoom = Math.max(MIN_ZOOM, props.zoom * (available / contentWidth));
  if (nextZoom < props.zoom) {
    emit("update:zoom", Number(nextZoom.toFixed(2)));
  }
}

async function loadScore(file: Blob): Promise<void> {
  if (!osmd) return;
  isRendering.value = true;
  try {
    await osmd.load(file);
    osmd.zoom = props.zoom;
    osmd.render();
    const pageCount = osmd.GraphicSheet?.MusicPages.length || 1;
    applyPageVisibility(pageCount, props.page);
    emit("loaded", pageCount);
    fitToContainer();
  } catch (error) {
    const message = error instanceof Error ? error.message : "Could not display this score.";
    emit("error", message);
  } finally {
    isRendering.value = false;
  }
}

onMounted(() => {
  if (!containerEl.value) return;

  osmd = new OpenSheetMusicDisplay(containerEl.value, {
    autoResize: false,
    backend: "svg",
    drawTitle: true,
    pageFormat: "A4_P",
  });

  if (props.file) {
    void loadScore(props.file);
  }

  resizeObserver = new ResizeObserver(() => {
    if (resizeTimeout) clearTimeout(resizeTimeout);
    resizeTimeout = setTimeout(fitToContainer, 150);
  });
  resizeObserver.observe(containerEl.value);
});

onBeforeUnmount(() => {
  resizeObserver?.disconnect();
  if (resizeTimeout) clearTimeout(resizeTimeout);
  try {
    osmd?.clear();
  } catch {
    // Container may already be detached; nothing left to clean up.
  }
  osmd = null;
});

watch(
  () => props.file,
  (file) => {
    if (file) void loadScore(file);
  },
);

watch(
  () => props.zoom,
  (zoom) => {
    if (!osmd) return;
    osmd.zoom = zoom;
    osmd.render();
    const pageCount = osmd.GraphicSheet?.MusicPages.length || 1;
    applyPageVisibility(pageCount, props.page);
  },
);

watch(
  () => props.page,
  (page) => {
    if (!osmd) return;
    const pageCount = osmd.GraphicSheet?.MusicPages.length || 1;
    applyPageVisibility(pageCount, page);
  },
);
</script>

<template>
  <div class="relative w-full">
    <p v-if="isRendering" class="absolute right-2 top-2 text-xs text-slate-400">Rendering…</p>
    <div
      ref="containerEl"
      class="osmd-score max-h-[75vh] w-full overflow-auto rounded-lg border border-slate-200 bg-white p-4"
    />
  </div>
</template>
