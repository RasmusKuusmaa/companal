<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";

import { BaseCard } from "@/shared/components/base";
import { toApiProblem } from "@/shared/utils/api-error";

import { projectsApi } from "../api/projects.api";
import type { Version } from "../types";
import MusicToolbar from "./MusicToolbar.vue";
import ScoreViewer from "./ScoreViewer.vue";

const MIN_ZOOM = 0.25;
const MAX_ZOOM = 3;
const ZOOM_STEP = 0.15;

const props = defineProps<{
  compositionId: string;
  versionId?: string;
}>();

const versions = ref<Version[]>([]);
const selectedVersionId = ref<string | null>(props.versionId ?? null);
const fileBlob = ref<Blob | null>(null);

const zoom = ref(1);
const page = ref(1);
const pageCount = ref(1);

const isLoadingVersions = ref(true);
const isLoadingFile = ref(false);
const loadError = ref("");
const viewerError = ref("");

const selectedVersion = computed(
  () => versions.value.find((v) => v.id === selectedVersionId.value) ?? null,
);

function clampZoom(value: number): number {
  return Math.min(MAX_ZOOM, Math.max(MIN_ZOOM, value));
}

async function loadFile(): Promise<void> {
  if (!selectedVersionId.value) return;
  isLoadingFile.value = true;
  viewerError.value = "";
  fileBlob.value = null;
  page.value = 1;
  try {
    fileBlob.value = await projectsApi.downloadVersion(
      props.compositionId,
      selectedVersionId.value,
    );
  } catch (error) {
    viewerError.value = toApiProblem(error).detail ?? "Could not load this score.";
  } finally {
    isLoadingFile.value = false;
  }
}

async function loadVersions(): Promise<void> {
  isLoadingVersions.value = true;
  loadError.value = "";
  try {
    versions.value = await projectsApi.listVersions(props.compositionId);
    if (!versions.value.length) {
      loadError.value = "No versions uploaded yet.";
      return;
    }
    const requested = props.versionId ? versions.value.find((v) => v.id === props.versionId) : null;
    const latest = versions.value.reduce((a, b) => (a.versionNumber > b.versionNumber ? a : b));
    selectedVersionId.value = (requested ?? latest).id;
    await loadFile();
  } catch (error) {
    loadError.value = toApiProblem(error).detail ?? "Could not load version history.";
  } finally {
    isLoadingVersions.value = false;
  }
}

onMounted(loadVersions);

watch(selectedVersionId, (id, previousId) => {
  if (id && id !== previousId) void loadFile();
});

function handleScoreLoaded(count: number): void {
  pageCount.value = count;
  if (page.value > count) page.value = count;
}

function handleScoreError(message: string): void {
  viewerError.value = message;
}

function zoomIn(): void {
  zoom.value = clampZoom(zoom.value + ZOOM_STEP);
}

function zoomOut(): void {
  zoom.value = clampZoom(zoom.value - ZOOM_STEP);
}

function zoomReset(): void {
  zoom.value = 1;
}

function prevPage(): void {
  if (page.value > 1) page.value -= 1;
}

function nextPage(): void {
  if (page.value < pageCount.value) page.value += 1;
}
</script>

<template>
  <section class="flex flex-col gap-4">
    <p v-if="isLoadingVersions" class="text-sm text-slate-500">Loading score…</p>

    <BaseCard v-else-if="loadError">
      <p class="text-sm text-red-600">{{ loadError }}</p>
    </BaseCard>

    <template v-else>
      <div
        v-if="versions.length > 1"
        class="flex flex-wrap items-center gap-2 text-sm text-slate-600"
      >
        <label for="score-version-select" class="font-medium">Version</label>
        <select
          id="score-version-select"
          v-model="selectedVersionId"
          class="rounded-md border border-slate-300 px-2 py-1 text-sm focus:border-slate-500 focus:outline-none focus:ring-1 focus:ring-slate-500"
        >
          <option v-for="version in versions" :key="version.id" :value="version.id">
            v{{ version.versionNumber }} — {{ version.originalFilename }}
          </option>
        </select>
      </div>

      <MusicToolbar
        :zoom="zoom"
        :page="page"
        :page-count="pageCount"
        :disabled="isLoadingFile || !fileBlob"
        @zoom-in="zoomIn"
        @zoom-out="zoomOut"
        @zoom-reset="zoomReset"
        @prev-page="prevPage"
        @next-page="nextPage"
      />

      <p v-if="viewerError" class="text-sm text-red-600" role="alert">{{ viewerError }}</p>
      <p v-if="isLoadingFile" class="text-sm text-slate-500">
        Loading “{{ selectedVersion?.originalFilename }}”…
      </p>

      <ScoreViewer
        v-if="fileBlob"
        v-model:zoom="zoom"
        :file="fileBlob"
        :page="page"
        @loaded="handleScoreLoaded"
        @error="handleScoreError"
      />
    </template>
  </section>
</template>
