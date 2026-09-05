<script setup lang="ts">
import { onMounted, ref } from "vue";
import { useRouter } from "vue-router";

import { useAuthStore } from "@/features/auth/stores/auth.store";
import ContinueLearningCard from "@/features/learning/components/ContinueLearningCard.vue";
import CoverageSummaryCard from "@/features/learning/components/CoverageSummaryCard.vue";
import ProjectList from "@/features/projects/components/ProjectList.vue";
import { useProjectsStore } from "@/features/projects/stores/projects.store";
import { BaseButton, BaseCard } from "@/shared/components/base";
import { toApiProblem } from "@/shared/utils/api-error";

const router = useRouter();
const authStore = useAuthStore();
const projectsStore = useProjectsStore();

const loadError = ref("");

async function loadProjects(): Promise<void> {
  loadError.value = "";
  try {
    await projectsStore.fetchAll();
  } catch (error) {
    loadError.value = toApiProblem(error).detail ?? "Could not load your compositions.";
  }
}

onMounted(loadProjects);

async function handleLogout(): Promise<void> {
  await authStore.logout();
  await router.push("/login");
}
</script>

<template>
  <main class="min-h-screen bg-slate-50 px-4 py-10">
    <div class="mx-auto max-w-2xl">
      <div class="mb-6 flex items-center justify-between">
        <div>
          <h1 class="text-xl font-semibold text-slate-900">Compositions</h1>
          <p class="text-sm text-slate-500">Signed in as {{ authStore.user?.fullName }}</p>
        </div>
        <BaseButton variant="ghost" @click="handleLogout">Sign out</BaseButton>
      </div>

      <div class="mb-4">
        <ContinueLearningCard />
      </div>

      <div class="mb-4">
        <CoverageSummaryCard />
      </div>

      <BaseCard>
        <div class="mb-4 flex items-center justify-between">
          <h2 class="text-base font-semibold text-slate-900">Your projects</h2>
          <RouterLink to="/projects/new">
            <BaseButton>New composition</BaseButton>
          </RouterLink>
        </div>

        <p v-if="projectsStore.isLoading" class="text-sm text-slate-500">Loading…</p>
        <div v-else-if="loadError" class="space-y-3">
          <p class="text-sm text-red-600" role="alert">{{ loadError }}</p>
          <BaseButton variant="secondary" @click="loadProjects">Try again</BaseButton>
        </div>
        <ProjectList v-else :compositions="projectsStore.compositions" />
      </BaseCard>
    </div>
  </main>
</template>
