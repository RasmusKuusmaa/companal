<script setup lang="ts">
import { ref } from "vue";
import { useRouter } from "vue-router";

import { BaseButton, BaseCard, BaseInput } from "@/shared/components/base";
import { toApiProblem } from "@/shared/utils/api-error";

import { useAuthStore } from "../stores/auth.store";

const router = useRouter();
const authStore = useAuthStore();

const fullName = ref("");
const email = ref("");
const password = ref("");
const confirmPassword = ref("");
const errorMessage = ref("");
const isSubmitting = ref(false);

async function handleSubmit(): Promise<void> {
  errorMessage.value = "";

  if (password.value !== confirmPassword.value) {
    errorMessage.value = "Passwords do not match.";
    return;
  }
  if (password.value.length < 8) {
    errorMessage.value = "Password must be at least 8 characters.";
    return;
  }

  isSubmitting.value = true;
  try {
    await authStore.register({
      email: email.value,
      password: password.value,
      fullName: fullName.value,
    });
    await router.push("/");
  } catch (error) {
    errorMessage.value = toApiProblem(error).detail ?? "Could not create your account.";
  } finally {
    isSubmitting.value = false;
  }
}
</script>

<template>
  <main class="flex min-h-screen items-center justify-center bg-slate-50 px-4">
    <BaseCard title="Create an account" class="w-full max-w-sm">
      <form class="space-y-4" novalidate @submit.prevent="handleSubmit">
        <BaseInput v-model="fullName" label="Full name" autocomplete="name" required />
        <BaseInput
          v-model="email"
          label="Email"
          type="email"
          autocomplete="email"
          required
        />
        <BaseInput
          v-model="password"
          label="Password"
          type="password"
          autocomplete="new-password"
          required
        />
        <BaseInput
          v-model="confirmPassword"
          label="Confirm password"
          type="password"
          autocomplete="new-password"
          required
        />

        <p v-if="errorMessage" class="text-sm text-red-600" role="alert">
          {{ errorMessage }}
        </p>

        <BaseButton type="submit" class="w-full" :disabled="isSubmitting">
          {{ isSubmitting ? "Creating account…" : "Create account" }}
        </BaseButton>
      </form>

      <p class="mt-4 text-center text-sm text-slate-600">
        Already have an account?
        <RouterLink to="/login" class="font-medium text-slate-900 hover:underline">
          Sign in
        </RouterLink>
      </p>
    </BaseCard>
  </main>
</template>
