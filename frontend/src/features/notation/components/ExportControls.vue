<script setup lang="ts">
/**
 * Downloads the current score as a MusicXML file, for a student to open in
 * whatever notation software they already use.
 *
 * Self-contained (owns its own loading/error state) rather than emitting an
 * event for a parent to handle - every page that embeds the editor should
 * get this for free without wiring it up itself, the same way Undo/Redo
 * and Copy/Paste don't need a parent's help either.
 */
import { ref } from "vue";

import { toApiProblem } from "@/shared/utils/api-error";
import { triggerBlobDownload } from "@/shared/utils/download";

import { notationApi } from "../api";
import type { NotationDocument } from "../types";

const props = defineProps<{
  document: NotationDocument;
}>();

const isExporting = ref(false);
const exportError = ref("");

async function handleExport(): Promise<void> {
  if (isExporting.value) return;
  isExporting.value = true;
  exportError.value = "";
  try {
    const blob = await notationApi.exportMusicXml(props.document);
    triggerBlobDownload(blob, "score.musicxml");
  } catch (error) {
    exportError.value = toApiProblem(error).detail ?? "Could not export this score.";
  } finally {
    isExporting.value = false;
  }
}
</script>

<template>
  <div class="flex items-center gap-2">
    <button
      type="button"
      class="flex h-9 items-center gap-1.5 rounded-md border border-slate-200 bg-white px-3 text-sm font-medium text-slate-700 transition-colors hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-40"
      :disabled="isExporting"
      title="Download this score as MusicXML"
      @click="handleExport"
    >
      <span aria-hidden="true">⭳</span>
      {{ isExporting ? "Exporting…" : "Export MusicXML" }}
    </button>
    <p v-if="exportError" class="text-sm text-red-600" role="alert">{{ exportError }}</p>
  </div>
</template>
