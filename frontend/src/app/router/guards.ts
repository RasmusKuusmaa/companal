import type { Router } from "vue-router";

import { useAuthStore } from "@/features/auth/stores/auth.store";

export function registerGuards(router: Router): void {
  router.beforeEach(async (to) => {
    const authStore = useAuthStore();

    // Resolve the persisted session exactly once, on the first navigation
    // after app boot, rather than on every route change.
    if (authStore.status === "idle") {
      await authStore.bootstrap();
    }

    if (to.meta.requiresAuth && !authStore.isAuthenticated) {
      return { name: "login", query: { redirect: to.fullPath } };
    }

    if (to.meta.guestOnly && authStore.isAuthenticated) {
      return { name: "home" };
    }

    return true;
  });
}
