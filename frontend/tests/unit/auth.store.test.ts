import { createPinia, setActivePinia } from "pinia";
import { beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("@/features/auth/api/auth.api", () => ({
  authApi: {
    register: vi.fn(),
    login: vi.fn(),
    logout: vi.fn(),
    me: vi.fn(),
  },
}));

vi.mock("@/services/http", () => ({
  refreshAccessToken: vi.fn(),
}));

import { authApi } from "@/features/auth/api/auth.api";
import { useAuthStore } from "@/features/auth/stores/auth.store";
import { refreshAccessToken } from "@/services/http";
import { getAccessToken, setAccessToken, setRefreshToken } from "@/services/token-storage";

const mockUser = {
  id: "11111111-1111-1111-1111-111111111111",
  email: "student@example.com",
  fullName: "Ada Student",
  role: "student" as const,
  isActive: true,
};

describe("auth store", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    setAccessToken(null);
    setRefreshToken(null);
    vi.clearAllMocks();
  });

  it("starts unauthenticated with no persisted refresh token", async () => {
    const store = useAuthStore();
    await store.bootstrap();

    expect(store.status).toBe("unauthenticated");
    expect(store.isAuthenticated).toBe(false);
  });

  it("logs in, stores tokens, and loads the user", async () => {
    vi.mocked(authApi.login).mockResolvedValue({
      accessToken: "access-1",
      refreshToken: "refresh-1",
    });
    vi.mocked(authApi.me).mockResolvedValue(mockUser);

    const store = useAuthStore();
    await store.login({ email: mockUser.email, password: "secret" });

    expect(store.status).toBe("authenticated");
    expect(store.isAuthenticated).toBe(true);
    expect(store.user).toEqual(mockUser);
    expect(getAccessToken()).toBe("access-1");
  });

  it("clears state on logout and revokes the refresh token server-side", async () => {
    vi.mocked(authApi.login).mockResolvedValue({
      accessToken: "access-1",
      refreshToken: "refresh-1",
    });
    vi.mocked(authApi.me).mockResolvedValue(mockUser);
    vi.mocked(authApi.logout).mockResolvedValue(undefined);

    const store = useAuthStore();
    await store.login({ email: mockUser.email, password: "secret" });
    const logoutPromise = store.logout();

    expect(store.status).toBe("unauthenticated");
    expect(store.user).toBeNull();
    expect(getAccessToken()).toBeNull();

    await logoutPromise;
    expect(authApi.logout).toHaveBeenCalledWith("refresh-1");
  });

  it("clears local state on logout even if the revoke call fails", async () => {
    vi.mocked(authApi.login).mockResolvedValue({
      accessToken: "access-1",
      refreshToken: "refresh-1",
    });
    vi.mocked(authApi.me).mockResolvedValue(mockUser);
    vi.mocked(authApi.logout).mockRejectedValue(new Error("network error"));

    const store = useAuthStore();
    await store.login({ email: mockUser.email, password: "secret" });
    await expect(store.logout()).resolves.toBeUndefined();

    expect(store.status).toBe("unauthenticated");
    expect(store.user).toBeNull();
  });

  it("registers, then signs in with the same credentials", async () => {
    vi.mocked(authApi.register).mockResolvedValue(mockUser);
    vi.mocked(authApi.login).mockResolvedValue({
      accessToken: "access-1",
      refreshToken: "refresh-1",
    });
    vi.mocked(authApi.me).mockResolvedValue(mockUser);

    const store = useAuthStore();
    await store.register({ email: mockUser.email, password: "secret123", fullName: mockUser.fullName });

    expect(authApi.register).toHaveBeenCalledWith({
      email: mockUser.email,
      password: "secret123",
      fullName: mockUser.fullName,
    });
    expect(authApi.login).toHaveBeenCalledWith({ email: mockUser.email, password: "secret123" });
    expect(store.status).toBe("authenticated");
    expect(store.user).toEqual(mockUser);
  });

  it("does not attempt to sign in if registration fails", async () => {
    vi.mocked(authApi.register).mockRejectedValue(new Error("email already registered"));

    const store = useAuthStore();
    await expect(
      store.register({ email: mockUser.email, password: "secret123", fullName: mockUser.fullName }),
    ).rejects.toThrow();

    expect(authApi.login).not.toHaveBeenCalled();
  });

  it("resumes a session on bootstrap when a refresh token is persisted", async () => {
    setRefreshToken("refresh-1");
    vi.mocked(refreshAccessToken).mockResolvedValue("access-2");
    vi.mocked(authApi.me).mockResolvedValue(mockUser);

    const store = useAuthStore();
    await store.bootstrap();

    expect(store.status).toBe("authenticated");
    expect(store.user).toEqual(mockUser);
  });

  it("stays unauthenticated and clears tokens if login fails", async () => {
    vi.mocked(authApi.login).mockRejectedValue(new Error("bad credentials"));

    const store = useAuthStore();
    await expect(store.login({ email: "x@example.com", password: "wrong" })).rejects.toThrow();

    expect(store.status).toBe("unauthenticated");
    expect(getAccessToken()).toBeNull();
  });
});
