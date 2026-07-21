import { defineStore } from "pinia";
import { ref } from "vue";

import { projectsApi } from "../api/projects.api";
import type { Composition, CreateCompositionPayload, RenameCompositionPayload } from "../types";

/**
 * Owns the composition *list* (dashboard) so a rename/delete from the
 * project detail page is reflected without a refetch when the user
 * navigates back. The detail page fetches its own single composition and
 * version history directly through projectsApi instead of through this
 * store - those aren't shown anywhere else, so there's nothing to keep in
 * sync.
 */
export const useProjectsStore = defineStore("projects", () => {
  const compositions = ref<Composition[]>([]);
  const isLoading = ref(false);

  async function fetchAll(): Promise<void> {
    isLoading.value = true;
    try {
      compositions.value = await projectsApi.list();
    } finally {
      isLoading.value = false;
    }
  }

  async function create(payload: CreateCompositionPayload): Promise<Composition> {
    const composition = await projectsApi.create(payload);
    compositions.value = [composition, ...compositions.value];
    return composition;
  }

  async function rename(id: string, payload: RenameCompositionPayload): Promise<Composition> {
    const updated = await projectsApi.rename(id, payload);
    compositions.value = compositions.value.map((c) => (c.id === id ? updated : c));
    return updated;
  }

  async function remove(id: string): Promise<void> {
    await projectsApi.remove(id);
    compositions.value = compositions.value.filter((c) => c.id !== id);
  }

  return { compositions, isLoading, fetchAll, create, rename, remove };
});
