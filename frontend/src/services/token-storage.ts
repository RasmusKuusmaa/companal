/**
 * Framework-agnostic token holder, deliberately separate from the Pinia
 * auth store: services/http.ts needs to read/write tokens from its axios
 * interceptors, and importing the store there would create a cycle
 * (http.ts -> auth store -> auth api -> http.ts). Both sides import this
 * instead.
 *
 * The access token lives in memory only (lost on reload, re-acquired via
 * refresh) so it can't be read out of localStorage by an XSS payload. The
 * refresh token is persisted so a reload doesn't force a full re-login;
 * moving it into an httpOnly cookie set by the backend is the next
 * hardening step once that endpoint shape exists.
 */

const REFRESH_TOKEN_KEY = "cadence.refresh_token";

let accessToken: string | null = null;

export function getAccessToken(): string | null {
  return accessToken;
}

export function setAccessToken(token: string | null): void {
  accessToken = token;
}

export function getRefreshToken(): string | null {
  return localStorage.getItem(REFRESH_TOKEN_KEY);
}

export function setRefreshToken(token: string | null): void {
  if (token) {
    localStorage.setItem(REFRESH_TOKEN_KEY, token);
  } else {
    localStorage.removeItem(REFRESH_TOKEN_KEY);
  }
}
