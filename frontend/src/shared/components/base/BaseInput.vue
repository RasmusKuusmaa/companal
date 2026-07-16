<script setup lang="ts">
withDefaults(
  defineProps<{
    label?: string;
    type?: string;
    required?: boolean;
    autocomplete?: string;
    error?: string;
  }>(),
  {
    type: "text",
    required: false,
  },
);

const model = defineModel<string>({ required: true });
</script>

<template>
  <label class="block">
    <span v-if="label" class="mb-1 block text-sm font-medium text-slate-700">{{ label }}</span>
    <input
      v-model="model"
      :type="type"
      :required="required"
      :autocomplete="autocomplete"
      class="w-full rounded-md border border-slate-300 px-3 py-2 text-sm shadow-sm focus:border-slate-500 focus:outline-none focus:ring-1 focus:ring-slate-500"
      :class="{ 'border-red-400': error }"
    />
    <span v-if="error" class="mt-1 block text-xs text-red-600">{{ error }}</span>
  </label>
</template>
