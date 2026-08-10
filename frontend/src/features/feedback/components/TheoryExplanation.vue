<script setup lang="ts">
import type { TheoryLesson } from "../types";

defineProps<{
  theory: TheoryLesson;
}>();
</script>

<template>
  <div class="rounded-md border border-indigo-100 bg-indigo-50 p-3">
    <p class="text-xs font-semibold uppercase tracking-wide text-indigo-700">
      Theory &middot; {{ theory.concept }}
    </p>
    <p class="mt-1 text-sm text-indigo-900">{{ theory.lesson }}</p>
  </div>
</template>
