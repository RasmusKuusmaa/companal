<script setup lang="ts">
withDefaults(
  defineProps<{
    variant?: "primary" | "secondary" | "ghost";
    type?: "button" | "submit" | "reset";
    disabled?: boolean;
  }>(),
  {
    variant: "primary",
    type: "button",
    disabled: false,
  },
);
</script>

<template>
  <button
    :type="type"
    :disabled="disabled"
    class="inline-flex items-center justify-center rounded-md px-4 py-2 text-sm font-medium transition-colors disabled:cursor-not-allowed disabled:opacity-50"
    :class="{
      'bg-slate-900 text-white hover:bg-slate-700': variant === 'primary',
      'bg-slate-100 text-slate-900 hover:bg-slate-200': variant === 'secondary',
      'text-slate-600 hover:bg-slate-100': variant === 'ghost',
    }"
  >
    <slot />
  </button>
</template>
