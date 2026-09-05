<script setup lang="ts">
/**
 * A reference panel for every keyboard shortcut the editor answers to -
 * the mouse is the on-ramp (every one of these has a toolbar button too),
 * this is for the point where a student wants to stop reaching for it.
 */
import { onBeforeUnmount, watch } from "vue";

const props = defineProps<{
  open: boolean;
}>();

const emit = defineEmits<{
  (event: "close"): void;
}>();

/**
 * A window listener rather than a `@keydown.escape` on the dialog: the
 * dialog itself never receives focus (nothing inside it is focusable by
 * default apart from the close button), so a per-element listener would
 * only work if a student happened to tab to something inside first.
 */
function handleEscape(event: KeyboardEvent): void {
  if (event.key === "Escape") emit("close");
}

watch(
  () => props.open,
  (open) => {
    if (open) window.addEventListener("keydown", handleEscape);
    else window.removeEventListener("keydown", handleEscape);
  },
);

onBeforeUnmount(() => window.removeEventListener("keydown", handleEscape));

interface ShortcutGroup {
  title: string;
  shortcuts: { keys: string; description: string }[];
}

const GROUPS: ShortcutGroup[] = [
  {
    title: "Notes",
    shortcuts: [
      { keys: "C D E F G A B", description: "Enter that pitch letter at the cursor" },
      { keys: "1 – 6", description: "Whole, half, quarter, eighth, 16th, 32nd duration" },
      { keys: ".", description: "Cycle the augmentation dot (none, 1, 2)" },
      { keys: "R", description: "Toggle rest mode for the next note" },
    ],
  },
  {
    title: "Marks",
    shortcuts: [
      { keys: "T", description: "Tie the note before the cursor to the next" },
      { keys: "S", description: "Slur the note before the cursor to the next" },
      { keys: "K", description: "Force a beam break after the note before the cursor" },
      { keys: "U", description: "Staccato" },
      { keys: "V", description: "Accent" },
      { keys: "N", description: "Tenuto" },
      { keys: "M", description: "Marcato" },
    ],
  },
  {
    title: "Navigation and selection",
    shortcuts: [
      { keys: "← →", description: "Move the cursor left or right" },
      { keys: "Shift + ← →", description: "Extend the selection left or right" },
      { keys: "Backspace", description: "Delete the note before the cursor, or the selection" },
      { keys: "Delete", description: "Delete the note before the cursor, or the selection" },
    ],
  },
  {
    title: "Editing",
    shortcuts: [
      { keys: "Ctrl/Cmd + C", description: "Copy the selection" },
      { keys: "Ctrl/Cmd + V", description: "Paste at the cursor" },
      { keys: "Ctrl/Cmd + Z", description: "Undo" },
      { keys: "Ctrl/Cmd + Shift + Z", description: "Redo" },
    ],
  },
];
</script>

<template>
  <div
    v-if="open"
    class="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 p-4"
    @click.self="emit('close')"
  >
    <div
      role="dialog"
      aria-modal="true"
      aria-label="Keyboard shortcuts"
      class="max-h-[85vh] w-full max-w-lg overflow-y-auto rounded-lg border border-slate-200 bg-white p-6 shadow-lg"
    >
      <div class="flex items-center justify-between">
        <h2 class="text-lg font-semibold text-slate-900">Keyboard shortcuts</h2>
        <button
          type="button"
          class="rounded-md p-1 text-slate-500 hover:bg-slate-100 hover:text-slate-700"
          aria-label="Close"
          @click="emit('close')"
        >
          ✕
        </button>
      </div>

      <div class="mt-4 space-y-5">
        <section v-for="group in GROUPS" :key="group.title">
          <h3 class="text-xs font-semibold uppercase tracking-wide text-slate-500">
            {{ group.title }}
          </h3>
          <dl class="mt-2 space-y-1.5">
            <div
              v-for="shortcut in group.shortcuts"
              :key="shortcut.keys"
              class="flex items-baseline justify-between gap-4 text-sm"
            >
              <dt class="shrink-0 rounded border border-slate-200 bg-slate-50 px-1.5 py-0.5 font-mono text-xs text-slate-700">
                {{ shortcut.keys }}
              </dt>
              <dd class="text-right text-slate-600">{{ shortcut.description }}</dd>
            </div>
          </dl>
        </section>
      </div>
    </div>
  </div>
</template>
