<script setup lang="ts">
defineProps<{
  title?: string;
}>();
</script>

<template>
  <div class="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
    <h2 v-if="title" class="mb-4 text-base font-semibold text-slate-900">{{ title }}</h2>
    <slot />
  </div>
</template>
