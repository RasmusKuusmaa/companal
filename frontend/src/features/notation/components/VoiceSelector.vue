<script setup lang="ts">
/**
 * Which voice on the active staff keyboard and click entry targets, when
 * the staff carries more than one - most staves have exactly one voice, so
 * this stays hidden rather than showing a pointless single choice.
 *
 * Labelled by position (V1, V2, ...) rather than a role name like
 * "Soprano": a voice here is just MusicXML's `<voice>` number, and nothing
 * in the document says which one is which part - that's on the exercise's
 * own staff names, not the voice itself.
 */
import type { NotationVoice } from "../types";

defineProps<{
  voices: NotationVoice[];
  activeVoiceId: string;
}>();

const emit = defineEmits<{
  (event: "select", voiceId: string): void;
}>();
</script>

<template>
  <div
    v-if="voices.length > 1"
    class="flex items-center gap-1"
    role="group"
    aria-label="Active voice"
  >
    <button
      v-for="(voice, index) in voices"
      :key="voice.id"
      type="button"
      class="flex h-9 min-w-9 items-center justify-center rounded-md border px-2 text-sm font-medium transition-colors"
      :class="
        voice.id === activeVoiceId
          ? 'border-slate-900 bg-slate-900 text-white'
          : 'border-slate-200 bg-white text-slate-700 hover:bg-slate-50'
      "
      :aria-pressed="voice.id === activeVoiceId"
      @click="emit('select', voice.id)"
    >
      V{{ index + 1 }}
    </button>
  </div>
</template>
