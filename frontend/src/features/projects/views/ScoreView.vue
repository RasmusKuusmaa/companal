<script setup lang="ts">
import { useRoute } from "vue-router";

import CompositionWorkspace from "../components/CompositionWorkspace.vue";

const route = useRoute();

const compositionId = route.params.id as string;
const versionId = typeof route.query.version === "string" ? route.query.version : undefined;
</script>

<template>
  <main class="min-h-screen bg-slate-50 px-4 py-10">
    <div class="mx-auto max-w-4xl space-y-6">
      <RouterLink :to="`/projects/${compositionId}`" class="text-sm text-slate-600 hover:underline">
        &larr; Back to composition
      </RouterLink>

      <CompositionWorkspace :composition-id="compositionId" :version-id="versionId" />
    </div>
  </main>
</template>
