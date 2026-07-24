<script setup lang="ts">
import { onMounted, ref } from "vue";
import { useRoute, useRouter } from "vue-router";

import { BaseButton, BaseCard, BaseInput } from "@/shared/components/base";
import { toApiProblem } from "@/shared/utils/api-error";
import { triggerBlobDownload } from "@/shared/utils/download";
import { formatBytes, formatDate } from "@/shared/utils/format";

import { projectsApi } from "../api/projects.api";
import { useProjectsStore } from "../stores/projects.store";
import type { Composition, Version } from "../types";

const route = useRoute();
const router = useRouter();
const projectsStore = useProjectsStore();

const compositionId = route.params.id as string;

const composition = ref<Composition | null>(null);
const versions = ref<Version[]>([]);
const loadError = ref("");
const isLoading = ref(true);

const isEditingTitle = ref(false);
const titleDraft = ref("");
const renameError = ref("");

const selectedFile = ref<File | null>(null);
const uploadError = ref("");
const isUploading = ref(false);

const downloadError = ref("");

async function loadComposition(): Promise<void> {
  isLoading.value = true;
  loadError.value = "";
  try {
    const [fetchedComposition, fetchedVersions] = await Promise.all([
      projectsApi.get(compositionId),
      projectsApi.listVersions(compositionId),
    ]);
    composition.value = fetchedComposition;
    versions.value = fetchedVersions;
  } catch (error) {
    loadError.value = toApiProblem(error).detail ?? "Could not load this composition.";
  } finally {
    isLoading.value = false;
  }
}

onMounted(loadComposition);

function startEditingTitle(): void {
  if (!composition.value) return;
  titleDraft.value = composition.value.title;
  renameError.value = "";
  isEditingTitle.value = true;
}

async function saveTitle(): Promise<void> {
  renameError.value = "";
  try {
    composition.value = await projectsStore.rename(compositionId, { title: titleDraft.value });
    isEditingTitle.value = false;
  } catch (error) {
    renameError.value = toApiProblem(error).detail ?? "Could not rename this composition.";
  }
}

async function handleDelete(): Promise<void> {
  if (!composition.value) return;
  const confirmed = window.confirm(`Delete "${composition.value.title}"? This cannot be undone.`);
  if (!confirmed) return;

  await projectsStore.remove(compositionId);
  await router.push("/");
}

function handleFileChange(event: Event): void {
  const input = event.target as HTMLInputElement;
  selectedFile.value = input.files?.[0] ?? null;
}

async function handleUpload(): Promise<void> {
  if (!selectedFile.value) return;
  uploadError.value = "";
  isUploading.value = true;
  try {
    await projectsApi.uploadVersion(compositionId, selectedFile.value);
    selectedFile.value = null;
    await loadComposition();
  } catch (error) {
    uploadError.value = toApiProblem(error).detail ?? "Could not upload this file.";
  } finally {
    isUploading.value = false;
  }
}

async function handleDownload(version: Version): Promise<void> {
  downloadError.value = "";
  try {
    const blob = await projectsApi.downloadVersion(compositionId, version.id);
    triggerBlobDownload(blob, version.originalFilename);
  } catch {
    downloadError.value = "Could not download this version.";
  }
}
</script>

<template>
  <main class="min-h-screen bg-slate-50 px-4 py-10">
    <div class="mx-auto max-w-2xl space-y-6">
      <RouterLink to="/" class="text-sm text-slate-600 hover:underline">
        &larr; Back to dashboard
      </RouterLink>

      <p v-if="isLoading" class="text-sm text-slate-500">Loading…</p>
      <BaseCard v-else-if="loadError" title="Composition">
        <p class="text-sm text-red-600">{{ loadError }}</p>
      </BaseCard>

      <template v-else-if="composition">
        <BaseCard>
          <div class="flex items-start justify-between gap-4">
            <div class="flex-1">
              <div v-if="isEditingTitle" class="space-y-2">
                <BaseInput v-model="titleDraft" label="Title" />
                <p v-if="renameError" class="text-sm text-red-600" role="alert">
                  {{ renameError }}
                </p>
                <div class="flex gap-2">
                  <BaseButton @click="saveTitle">Save</BaseButton>
                  <BaseButton variant="ghost" @click="isEditingTitle = false">Cancel</BaseButton>
                </div>
              </div>
              <div v-else>
                <h1 class="text-xl font-semibold text-slate-900">{{ composition.title }}</h1>
                <p class="text-sm text-slate-500">
                  {{ composition.versionCount }}
                  {{ composition.versionCount === 1 ? "version" : "versions" }} · updated
                  {{ formatDate(composition.updatedAt) }}
                </p>
              </div>
            </div>
            <div v-if="!isEditingTitle" class="flex gap-2">
              <RouterLink
                v-if="versions.length"
                v-slot="{ navigate }"
                :to="`/projects/${compositionId}/score`"
                custom
              >
                <BaseButton variant="secondary" @click="navigate">View score</BaseButton>
              </RouterLink>
              <BaseButton variant="secondary" @click="startEditingTitle">Rename</BaseButton>
              <BaseButton variant="ghost" @click="handleDelete">Delete</BaseButton>
            </div>
          </div>
        </BaseCard>

        <BaseCard title="Upload a new version">
          <div class="flex items-center gap-2">
            <input
              type="file"
              accept=".xml,.musicxml,.mxl"
              class="flex-1 text-sm text-slate-600"
              @change="handleFileChange"
            />
            <BaseButton :disabled="!selectedFile || isUploading" @click="handleUpload">
              {{ isUploading ? "Uploading…" : "Upload" }}
            </BaseButton>
          </div>
          <p v-if="uploadError" class="mt-2 text-sm text-red-600" role="alert">
            {{ uploadError }}
          </p>
        </BaseCard>

        <BaseCard title="Version history">
          <p v-if="downloadError" class="mb-2 text-sm text-red-600" role="alert">
            {{ downloadError }}
          </p>
          <ul v-if="versions.length" class="divide-y divide-slate-200">
            <li
              v-for="version in versions"
              :key="version.id"
              class="flex items-center justify-between py-3"
            >
              <div>
                <p class="font-medium text-slate-900">
                  v{{ version.versionNumber }} — {{ version.originalFilename }}
                </p>
                <p class="text-sm text-slate-500">
                  {{ formatBytes(version.fileSize) }} · {{ formatDate(version.createdAt) }}
                </p>
              </div>
              <div class="flex gap-2">
                <RouterLink
                  v-slot="{ navigate }"
                  :to="`/projects/${compositionId}/score?version=${version.id}`"
                  custom
                >
                  <BaseButton variant="secondary" @click="navigate">View</BaseButton>
                </RouterLink>
                <BaseButton variant="secondary" @click="handleDownload(version)">
                  Download
                </BaseButton>
              </div>
            </li>
          </ul>
          <p v-else class="text-sm text-slate-500">No versions uploaded yet.</p>
        </BaseCard>
      </template>
    </div>
  </main>
</template>
