import { defineStore } from "pinia";
import { computed, ref } from "vue";

import { refreshAccessToken } from "@/services/http";
import {
  getAccessToken,
  getRefreshToken,
  setAccessToken,
  setRefreshToken,
} from "@/services/token-storage";

import { authApi } from "../api/auth.api";
import type { LoginPayload, User } from "../types";

export type AuthStatus = "idle" | "authenticating" | "authenticated" | "unauthenticated";

export const useAuthStore = defineStore("auth", () => {
  const user = ref<User | null>(null);
  const status = ref<AuthStatus>("idle");

  const isAuthenticated = computed(
    () => status.value === "authenticated" && getAccessToken() !== null,
  );

  async function login(payload: LoginPayload): Promise<void> {
    status.value = "authenticating";
    try {
      const tokens = await authApi.login(payload);
      setAccessToken(tokens.accessToken);
      setRefreshToken(tokens.refreshToken);
      user.value = await authApi.me();
      status.value = "authenticated";
    } catch (error) {
      setAccessToken(null);
      setRefreshToken(null);
      user.value = null;
      status.value = "unauthenticated";
      throw error;
    }
  }

  function logout(): void {
    setAccessToken(null);
    setRefreshToken(null);
    user.value = null;
    status.value = "unauthenticated";
  }

  /**
   * Called once on app boot (from the router's first navigation guard) to
   * silently resume a session from the persisted refresh token, so a page
   * reload doesn't force the user back to the login screen.
   */
  async function bootstrap(): Promise<void> {
    if (!getRefreshToken()) {
      status.value = "unauthenticated";
      return;
    }

    const token = await refreshAccessToken();
    if (!token) {
      status.value = "unauthenticated";
      return;
    }

    try {
      user.value = await authApi.me();
      status.value = "authenticated";
    } catch {
      logout();
    }
  }

  return { user, status, isAuthenticated, login, logout, bootstrap };
});
