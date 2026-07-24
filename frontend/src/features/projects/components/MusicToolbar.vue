<script setup lang="ts">
import { BaseButton } from "@/shared/components/base";

withDefaults(
  defineProps<{
    zoom: number;
    page: number;
    pageCount: number;
    disabled?: boolean;
  }>(),
  {
    disabled: false,
  },
);

const emit = defineEmits<{
  "zoom-in": [];
  "zoom-out": [];
  "zoom-reset": [];
  "prev-page": [];
  "next-page": [];
}>();
</script>

<template>
  <div
    class="flex flex-wrap items-center justify-between gap-3 rounded-lg border border-slate-200 bg-white px-4 py-2"
  >
    <div class="flex items-center gap-1">
      <BaseButton
        variant="ghost"
        :disabled="disabled"
        aria-label="Zoom out"
        @click="emit('zoom-out')"
      >
        &minus;
      </BaseButton>
      <button
        type="button"
        class="min-w-[3.5rem] rounded-md px-2 py-1 text-sm text-slate-600 hover:bg-slate-100"
        :disabled="disabled"
        @click="emit('zoom-reset')"
      >
        {{ Math.round(zoom * 100) }}%
      </button>
      <BaseButton
        variant="ghost"
        :disabled="disabled"
        aria-label="Zoom in"
        @click="emit('zoom-in')"
      >
        &plus;
      </BaseButton>
    </div>

    <div class="flex items-center gap-1">
      <BaseButton
        variant="ghost"
        :disabled="disabled || page <= 1"
        aria-label="Previous page"
        @click="emit('prev-page')"
      >
        &lsaquo; Prev
      </BaseButton>
      <span class="min-w-[6rem] text-center text-sm text-slate-600">
        Page {{ pageCount ? page : 0 }} of {{ pageCount }}
      </span>
      <BaseButton
        variant="ghost"
        :disabled="disabled || page >= pageCount"
        aria-label="Next page"
        @click="emit('next-page')"
      >
        Next &rsaquo;
      </BaseButton>
    </div>
  </div>
</template>
