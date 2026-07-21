<script setup lang="ts">
import { useRouter } from "vue-router";

import { useAuthStore } from "@/features/auth/stores/auth.store";
import { BaseButton, BaseCard } from "@/shared/components/base";

const router = useRouter();
const authStore = useAuthStore();

async function handleLogout(): Promise<void> {
  await authStore.logout();
  await router.push("/login");
}
</script>

<template>
  <main class="flex min-h-screen items-center justify-center bg-slate-50 px-4">
    <BaseCard title="Home" class="w-full max-w-sm">
      <p class="text-slate-600">Welcome, {{ authStore.user?.fullName }}.</p>
      <BaseButton variant="secondary" class="mt-4 w-full" @click="handleLogout">
        Sign out
      </BaseButton>
    </BaseCard>
  </main>
</template>
