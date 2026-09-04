<script setup lang="ts">
/**
 * Which staff keyboard and click entry targets, when there's more than one.
 *
 * Hidden entirely for the overwhelmingly common single-staff exercise - a
 * one-button choice would only clutter that toolbar. Clicking a staff on
 * the score already moves entry there (see `NotationEditor`'s handling of
 * `StaffClick`); this is for reaching a staff that has nothing on it yet to
 * click, most often right after opening a grand-staff template.
 */
import type { NotationStaff } from "../types";

defineProps<{
  staves: NotationStaff[];
  activeStaffIndex: number;
}>();

const emit = defineEmits<{
  (event: "select", staffIndex: number): void;
}>();
</script>

<template>
  <div
    v-if="staves.length > 1"
    class="flex flex-wrap items-center gap-1"
    role="group"
    aria-label="Active staff"
  >
    <button
      v-for="(staff, index) in staves"
      :key="staff.id"
      type="button"
      class="flex h-9 items-center rounded-md border px-3 text-sm font-medium transition-colors"
      :class="
        index === activeStaffIndex
          ? 'border-slate-900 bg-slate-900 text-white'
          : 'border-slate-200 bg-white text-slate-700 hover:bg-slate-50'
      "
      :aria-pressed="index === activeStaffIndex"
      @click="emit('select', index)"
    >
      {{ staff.name ?? `Staff ${index + 1}` }}
    </button>
  </div>
</template>
