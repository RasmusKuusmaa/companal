<script setup lang="ts">
/**
 * What free actually includes, honestly - per the build plan's design
 * decisions: every lesson, quiz, and deterministic grade is free forever,
 * nothing is locked, and only AI commentary is tiered - free still gets a
 * real monthly quota, not a locked demo.
 *
 * Premium has no working checkout yet - Stripe isn't wired in (see
 * `billing.models`'s module docstring) - so its button stays disabled
 * rather than promising something this page can't deliver.
 */
import { BaseButton, BaseCard } from "@/shared/components/base";
</script>

<template>
  <main class="min-h-screen bg-slate-50 px-4 py-10">
    <div class="mx-auto max-w-3xl">
      <div class="mb-8 text-center">
        <h1 class="text-2xl font-semibold text-slate-900">Pricing</h1>
        <p class="mt-2 text-sm text-slate-600">
          The theory curriculum is free forever. Only AI commentary is tiered.
        </p>
      </div>

      <div class="grid gap-6 sm:grid-cols-2">
        <BaseCard>
          <h2 class="text-lg font-semibold text-slate-900">Free</h2>
          <p class="mt-1 text-sm text-slate-500">For every serious student, no card required.</p>
          <ul class="mt-4 space-y-2 text-sm text-slate-700">
            <li>Every stage, lesson, and quiz - nothing locked</li>
            <li>Unlimited composition attempts, all graded and kept forever</li>
            <li>Full deterministic grading: rules, checklists, and analysis</li>
            <li>5 AI feedback or grading requests every month</li>
          </ul>
        </BaseCard>

        <BaseCard>
          <h2 class="text-lg font-semibold text-slate-900">Premium</h2>
          <p class="mt-1 text-sm text-slate-500">For unlimited AI commentary.</p>
          <ul class="mt-4 space-y-2 text-sm text-slate-700">
            <li>Everything in Free</li>
            <li>Unlimited AI feedback and exercise grading</li>
            <li>AI-written rubric commentary on exams</li>
          </ul>
          <BaseButton class="mt-4 w-full" disabled>Coming soon</BaseButton>
        </BaseCard>
      </div>
    </div>
  </main>
</template>
