<script setup lang="ts">
import { formatDate } from "@/shared/utils/format";

import type { Composition } from "../types";

defineProps<{
  compositions: Composition[];
}>();
</script>

<template>
  <ul v-if="compositions.length" class="divide-y divide-slate-200">
    <li v-for="composition in compositions" :key="composition.id">
      <RouterLink
        :to="`/projects/${composition.id}`"
        class="flex items-center justify-between py-3 hover:bg-slate-50"
      >
        <div>
          <p class="font-medium text-slate-900">{{ composition.title }}</p>
          <p class="text-sm text-slate-500">Updated {{ formatDate(composition.updatedAt) }}</p>
        </div>
        <span class="text-sm text-slate-500">
          {{ composition.versionCount }}
          {{ composition.versionCount === 1 ? "version" : "versions" }}
        </span>
      </RouterLink>
    </li>
  </ul>
  <p v-else class="text-sm text-slate-500">No compositions yet.</p>
</template>
