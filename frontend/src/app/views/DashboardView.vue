<script setup lang="ts">
import { onMounted } from "vue";
import { useRouter } from "vue-router";

import { useAuthStore } from "@/features/auth/stores/auth.store";
import ProjectList from "@/features/projects/components/ProjectList.vue";
import { useProjectsStore } from "@/features/projects/stores/projects.store";
import { BaseButton, BaseCard } from "@/shared/components/base";

const router = useRouter();
const authStore = useAuthStore();
const projectsStore = useProjectsStore();

onMounted(() => {
  void projectsStore.fetchAll();
});

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

      <BaseCard>
        <div class="mb-4 flex items-center justify-between">
          <h2 class="text-base font-semibold text-slate-900">Your projects</h2>
          <RouterLink to="/projects/new">
            <BaseButton>New composition</BaseButton>
          </RouterLink>
        </div>

        <p v-if="projectsStore.isLoading" class="text-sm text-slate-500">Loading…</p>
        <ProjectList v-else :compositions="projectsStore.compositions" />
      </BaseCard>
    </div>
  </main>
</template>
