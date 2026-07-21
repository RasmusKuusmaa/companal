<script setup lang="ts">
import { ref } from "vue";
import { useRouter } from "vue-router";

import { BaseButton, BaseCard, BaseInput } from "@/shared/components/base";
import { toApiProblem } from "@/shared/utils/api-error";

import { useProjectsStore } from "../stores/projects.store";

const router = useRouter();
const projectsStore = useProjectsStore();

const title = ref("");
const errorMessage = ref("");
const isSubmitting = ref(false);

async function handleSubmit(): Promise<void> {
  errorMessage.value = "";
  isSubmitting.value = true;
  try {
    const composition = await projectsStore.create({ title: title.value });
    await router.push(`/projects/${composition.id}`);
  } catch (error) {
    errorMessage.value = toApiProblem(error).detail ?? "Could not create this composition.";
  } finally {
    isSubmitting.value = false;
  }
}
</script>

<template>
  <main class="flex min-h-screen items-center justify-center bg-slate-50 px-4">
    <BaseCard title="New composition" class="w-full max-w-sm">
      <form class="space-y-4" novalidate @submit.prevent="handleSubmit">
        <BaseInput v-model="title" label="Title" required autocomplete="off" />

        <p v-if="errorMessage" class="text-sm text-red-600" role="alert">
          {{ errorMessage }}
        </p>

        <div class="flex items-center gap-2">
          <BaseButton type="submit" :disabled="isSubmitting">
            {{ isSubmitting ? "Creating…" : "Create" }}
          </BaseButton>
          <RouterLink to="/">
            <BaseButton variant="ghost" type="button">Cancel</BaseButton>
          </RouterLink>
        </div>
      </form>
    </BaseCard>
  </main>
</template>
