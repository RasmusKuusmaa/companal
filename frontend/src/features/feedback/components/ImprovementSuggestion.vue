<script setup lang="ts">
defineProps<{
  text: string;
}>();
</script>

<template>
  <div class="rounded-md border border-emerald-100 bg-emerald-50 p-3">
    <p class="text-xs font-semibold uppercase tracking-wide text-emerald-700">Try this</p>
    <p class="mt-1 text-sm text-emerald-900">{{ text }}</p>
  </div>
</template>
