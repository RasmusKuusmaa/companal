<script setup lang="ts">
import ImprovementSuggestion from "./ImprovementSuggestion.vue";
import TheoryExplanation from "./TheoryExplanation.vue";
import type { FeedbackIssue } from "../types";

defineProps<{
  issue: FeedbackIssue;
}>();
</script>

<template>
  <div class="space-y-3 rounded-lg border border-slate-200 p-4">
    <div>
      <p class="font-medium text-slate-900">{{ issue.problem }}</p>
      <p class="mt-1 text-sm text-slate-600">{{ issue.explanation }}</p>
    </div>
    <ImprovementSuggestion :text="issue.suggestion" />
    <TheoryExplanation :theory="issue.theory" />
  </div>
</template>
