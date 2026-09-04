<script setup lang="ts">
/**
 * A passage of lesson prose.
 *
 * `v-html` is deliberate and safe here: the string it receives has been
 * through `renderMarkdown`, which sanitizes unconditionally (see that
 * module for why it does so even though lesson content is authored in the
 * repository). Rendering the markdown as text instead would defeat the
 * point - theory content is headings, tables and emphasis.
 */
import { computed } from "vue";

import { renderMarkdown } from "@/shared/utils/markdown";

import type { ReadingStep } from "../types";

const props = defineProps<{ step: ReadingStep }>();

const html = computed(() => renderMarkdown(props.step.markdown));
</script>

<template>
  <!-- eslint-disable-next-line vue/no-v-html -- sanitized in renderMarkdown -->
  <article class="prose-lesson" v-html="html" />
</template>
