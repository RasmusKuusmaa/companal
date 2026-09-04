<script setup lang="ts">
/**
 * Play/stop and tempo, for hearing back what's on the staff.
 *
 * Tempo lives on the document itself (see NotationDocument.tempo), not as
 * separate playback-only state, so a tempo the student sets sticks with the
 * exercise the same way a key signature does - it's part of what they wrote,
 * not a preference for how they happened to listen to it once.
 */
const props = defineProps<{
  isPlaying: boolean;
  tempo: number;
}>();

const emit = defineEmits<{
  (event: "play"): void;
  (event: "stop"): void;
  (event: "update:tempo", value: number): void;
}>();

function handleTempoInput(event: Event): void {
  const value = Number((event.target as HTMLInputElement).value);
  if (Number.isFinite(value)) emit("update:tempo", value);
}
</script>

<template>
  <div class="flex items-center gap-3">
    <button
      type="button"
      class="flex h-9 items-center gap-1.5 rounded-md border border-slate-200 bg-white px-3 text-sm font-medium text-slate-700 transition-colors hover:bg-slate-50"
      @click="props.isPlaying ? emit('stop') : emit('play')"
    >
      <span aria-hidden="true">{{ props.isPlaying ? "⏹" : "▶" }}</span>
      {{ props.isPlaying ? "Stop" : "Play" }}
    </button>

    <label class="flex items-center gap-2 text-sm text-slate-600">
      <span class="sr-only">Tempo, in quarter notes per minute</span>
      <input
        type="number"
        min="20"
        max="300"
        step="1"
        :value="tempo"
        class="w-16 rounded-md border border-slate-200 px-2 py-1 text-sm focus:border-slate-500 focus:outline-none focus:ring-1 focus:ring-slate-500"
        @change="handleTempoInput"
      />
      <span>bpm</span>
    </label>
  </div>
</template>
