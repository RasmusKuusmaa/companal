/**
 * Shared axios client. Two responsibilities live here on purpose, both
 * because they need to run underneath every feature's API module:
 *
 *  1. Attach the current access token to every request.
 *  2. On a 401, refresh once and retry the original request.
 *
 * The refresh call itself goes through a bare, non-intercepted axios
 * instance (`refreshClient`) so it can never recursively trigger its own
 * 401 handling, and concurrent 401s are collapsed into a single in-flight
 * refresh (`refreshPromise`) so a burst of requests doesn't race to rotate
 * the refresh token multiple times.
 */

import axios, { type InternalAxiosRequestConfig } from "axios";

import { getAccessToken, getRefreshToken, setAccessToken, setRefreshToken } from "./token-storage";

declare module "axios" {
  interface InternalAxiosRequestConfig {
    _retried?: boolean;
  }
}

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "/api/v1";

export const httpClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 15_000,
});

const refreshClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 15_000,
});

interface TokenResponseDto {
  access_token: string;
  refresh_token: string;
}

let refreshPromise: Promise<string | null> | null = null;

export async function refreshAccessToken(): Promise<string | null> {
  const refreshToken = getRefreshToken();
  if (!refreshToken) {
    return null;
  }

  if (!refreshPromise) {
    refreshPromise = refreshClient
      .post<TokenResponseDto>("/auth/refresh", { refresh_token: refreshToken })
      .then(({ data }) => {
        setAccessToken(data.access_token);
        setRefreshToken(data.refresh_token);
        return data.access_token;
      })
      .catch(() => {
        setAccessToken(null);
        setRefreshToken(null);
        return null;
      })
      .finally(() => {
        refreshPromise = null;
      });
  }

  return refreshPromise;
}

httpClient.interceptors.request.use((config) => {
  const token = getAccessToken();
  if (token) {
    config.headers.set("Authorization", `Bearer ${token}`);
  }
  return config;
});

httpClient.interceptors.response.use(
  (response) => response,
  async (error: unknown) => {
    if (!axios.isAxiosError(error)) {
      return Promise.reject(error);
    }

    const originalRequest = error.config as InternalAxiosRequestConfig | undefined;
    const shouldAttemptRefresh =
      error.response?.status === 401 && originalRequest !== undefined && !originalRequest._retried;

    if (!shouldAttemptRefresh) {
      return Promise.reject(error);
    }

    const newAccessToken = await refreshAccessToken();
    if (!newAccessToken) {
      return Promise.reject(error);
    }

    originalRequest._retried = true;
    originalRequest.headers.set("Authorization", `Bearer ${newAccessToken}`);
    return httpClient(originalRequest);
  },
);
